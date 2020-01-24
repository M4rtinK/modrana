# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# A turn by turn navigation module.
#----------------------------------------------------------------------------
# Copyright 2007, Oliver White
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#---------------------------------------------------------------------------
from __future__ import with_statement

from modules.base_module import RanaModule
from core import geo
from core import threads
from core import constants
from core.signal import Signal
import math
import time
from threading import RLock

REROUTE_CHECK_INTERVAL = 5000  # in ms
# in m/s, about 46 km/h - if this speed is reached, the rerouting threshold is multiplied
# by REROUTING_THRESHOLD_MULTIPLIER
INCREASE_REROUTING_THRESHOLD_SPEED = 20
REROUTING_DEFAULT_THRESHOLD = 30
# not enabled at the moment - needs more field testing
REROUTING_THRESHOLD_MULTIPLIER = 1.0
# how many times needs the threshold be crossed to
# trigger rerouting
REROUTING_TRIGGER_COUNT = 3

MAX_CONSECUTIVE_AUTOMATIC_REROUTES = 3
AUTOMATIC_REROUTE_COUNTER_EXPIRATION_TIME = 600  # in seconds

def getModule(*args, **kwargs):
    return TurnByTurn(*args, **kwargs)


class TurnByTurn(RanaModule):
    """A turn by turn navigation module."""

    def __init__(self, *args, **kwargs):
        RanaModule.__init__(self, *args, **kwargs)
        # initial colors
        self.navigationBoxBackground = (0, 0, 1, 0.3)  # very transparent blue
        self.navigationBoxText = (1, 1, 1, 1)  # non-transparent white
        self._tbt_worker_lock = RLock()
        self._tbt_worker_enabled = False
        self._go_to_initial_state()
        self._automatic_reroute_counter = 0  # counts consecutive automatic reroutes
        self._last_automatic_reroute_timestamp = time.time()
        # reroute even though the route was not yet reached (for special cases)
        self._override_route_reached = False
        # signals
        self.navigation_started = Signal()
        self.navigation_stopped = Signal()
        self.destination_reached = Signal()
        self.rerouting_triggered = Signal()
        self.current_step_changed = Signal()

    def _go_to_initial_state(self):
        """restore initial state"""
        self._route = None
        self._current_step_index_value = 0
        self._current_step_indicator = None
        self._espeak_first_and_half_trigger = False
        self._espeak_first_trigger = False
        self._espeak_second_trigger = False
        self._current_distance = None
        self._current_step = None
        self._navigation_box_hidden = False
        self._m_route_length = 0
        self._location_watch_id = None
        self._on_route = False
        # rerouting is enabled once the route is reached for the first time
        self._route_reached = False
        self._rerouting_threshold_multiplier = 1.0
        self._rerouting_threshold_crossed_counter = 0

    def firstTime(self):
        icons = self.m.get('icons', None)
        if icons:
            icons.subscribeColorInfo(self, self._colors_changed_cb)

    def _colors_changed_cb(self, colors):
        self.navigationBoxBackground = colors['navigation_box_background'].getCairoColor()
        self.navigationBoxText = colors['navigation_box_text'].getCairoColor()

    def handleMessage(self, message, messageType, args):
        if message == 'start':
            if messageType == 'ms':
                self.start_tbt(from_where=args)
        elif message == 'stop':
            self.stop_tbt()
        elif message == 'reroute':  # manual rerouting
            # reset automatic reroute counter
            self._automatic_reroute_counter = 0
            self._reroute()
        elif message == "toggleBoxHiding":
            self.log.info("toggling navigation box visibility")
            self._navigation_box_hidden = not self._navigation_box_hidden
        elif message == "switchToPreviousTurn":
            self.switch_to_previous_step()
        elif message == "switchToNextTurn":
            self.switch_to_next_step()
        elif message == "showMessageInsideNotification":
            if self.current_step:
                message = "<i>turn description:</i>\n%s" % self.current_step.description
                if self.dmod.has_custom_notification_support:
                    self.dmod.notify(message, 7000)
                    # TODO: add support for modRana notifications once they support line wrapping

    def _reroute_auto(self):
        """This function is called when automatic rerouting is triggered."""

        # check time from last automatic reroute
        dt = time.time() - self._last_automatic_reroute_timestamp
        if dt >= AUTOMATIC_REROUTE_COUNTER_EXPIRATION_TIME:
            # reset the automatic reroute counter
            self._automatic_reroute_counter = 0
            self.log.debug('automatic reroute counter expired, clearing')

        # on some routes, when we are moving away from the start of the route, it
        # is needed to reroute a couple of times before the correct way is found
        # on the other hand there should be a limit on the number of times
        # modRana reroutes in a row
        #
        # SOLUTION:
        # 1. enable automatic rerouting even though the route was not yet reached
        # (as we are moving away from it)
        # 2. do this only a limited number of times (up to 3 times in a row)
        # 3. the counter is reset by manual rerouting, by reaching the route or after 10 minutes

        if self._automatic_reroute_counter < MAX_CONSECUTIVE_AUTOMATIC_REROUTES:
            self.log.debug('faking that route was reached to enable new rerouting')
            self._override_route_reached = True
        else:
            self.log.info('tbt: too many consecutive reroutes (%d),', self._automatic_reroute_counter)
            self.log.info('reach the route to enable automatic rerouting')
            self.log.info('or reroute manually')

        # increment the automatic reroute counter & update the timestamp
        self._automatic_reroute_counter += 1
        self._last_automatic_reroute_timestamp = time.time()

        # trigger rerouting
        self._reroute()
        self.rerouting_triggered()

    def _reroute(self):
        # 1. say rerouting is in progress
        voiceMessage = "rerouting"
        voice = self.m.get('voice', None)
        if voice:
            voice.say(voiceMessage, "en")  # make sure rerouting said with english voice
        time.sleep(2)  # TODO: improve this

        route = self.m.get('route', None)
        if route:
            # 2. get a new route from current position to destination
            route.reroute()
        # 3. restart routing for to this new route from the closest point
        self.sendMessage("ms:turnByTurn:start:closest")

    @property
    def automatic_rerouting_enabled(self):
        """Report if automatic rerouting is enabled.

        Automatic rerouting is considered to be enabled if the reroutingThreshold key
        holds a value that is not None (in general a string representation of a floating
        point number).

        :return: if automatic rerouting is enabled
        :rtype: bool
        """
        return self.get('reroutingThreshold', REROUTING_DEFAULT_THRESHOLD)

    def _say_turn(self, message, distanceInMeters, force_language_code=False):
        """Say a text-to-speech message about a turn.

        This basically wraps the simple say method from voice and adds some more information,
        like current distance to the turn.
        """
        voice = self.m.get('voice', None)
        units = self.m.get('units', None)

        if voice and units:
            (dist_string, short, long) = units.humanRound(distanceInMeters)

            if dist_string == "0":
                dist_string = ""
            else:
                dist_string = '<p xml:lang="en">in <emphasis level="strong">' + dist_string + ' ' + long + '</emphasis></p><br>'
                # TODO: language specific distance strings
            text = dist_string + message

            #      """ the message can contain unicode, this might cause an exception when printing it
            #      in some systems (SHR-u on Neo, for example)"""
            #      try:
            #        print("saying: %s" % text)
            #        pass
            #      except UnicodeEncodeError:
            #        print("voice: printing the current message to stdout failed do to unicode conversion error")

            if force_language_code:
                espeak_language_code = force_language_code
            else:
                # the espeak language code is the first part of this whitespace delimited string
                espeak_language_code = self.get('directionsLanguage', 'en en').split(" ")[0]
            return voice.say(text, espeak_language_code)

    @property
    def _max_step_index(self):
        return self._route.message_point_count - 1

    def _get_starting_step(self, which='first'):
        if self._route:
            if which == 'first':
                return self._get_step(0)
            if which == 'closest':
                return self._get_closest_step()

    def _get_closest_step(self):
        """Get the geographically closest step."""
        proj = self.m.get('projection', None)  # we also need the projection module
        pos = self.get('pos', None)  # and current position
        if pos and proj:
            (lat1, lon1) = pos
            temp_steps = self._route.message_points
            for step in temp_steps:
                (lat2, lon2) = step.getLL()
                step.current_distance = geo.distance(lat1, lon1, lat2, lon2) * 1000  # km to m
            closest_step = sorted(temp_steps, key=lambda x: x.current_distance)[0]

            return closest_step

    def _get_step(self, index):
        """Return steps for valid index, None otherwise."""
        max_index = self._max_step_index
        if index > max_index or index < -(max_index + 1):
            self.log.error("wrong turn index: %d, max index is: %d", index, max_index)
            return None
        else:
            return self._route.get_message_point_by_index(index)

    def _get_step_index(self, step):
        return self._route.get_message_point_index(step)

    @property
    def current_step(self):
        """Return current step."""
        return self._route.get_message_point_by_index(self._current_step_index)

    @current_step.setter
    def current_step(self, step):
        """Set a given step as current step."""
        mp_index = self._route.get_message_point_index(step)
        self._current_step_index = mp_index
        self.current_step_changed(step)

    @property
    def _current_step_index(self):
        return self._current_step_index_value

    @_current_step_index.setter
    def _current_step_index(self, index):
        self._current_step_index_value = index
        # trigger a navigation update every time current step index is set
        self._do_navigation_update()

    def switch_to_previous_step(self):
        """Switch to previous step and clean up."""
        next_index = self._current_step_index - 1
        if next_index >= 0:
            self._current_step_index = next_index
            self._espeak_first_trigger = False
            self._espeak_second_trigger = False
            self.log.info("switching to previous step")
            self.current_step_changed(self.current_step)
        else:
            self.log.info("previous step reached")

    def switch_to_next_step(self):
        """Switch to next step and clean up."""
        max_index = self._max_step_index
        next_index = self._current_step_index + 1
        if next_index <= max_index:
            self._current_step_index = next_index
            self._espeak_first_and_half_trigger = False
            self._espeak_first_trigger = False
            self._espeak_second_trigger = False
            self.log.info("switching to next step")
            self.current_step_changed(self.current_step)
        else:
            self.log.info("last step reached")
            self._last_step_reached()

    def _last_step_reached(self):
        """Handle all tasks that are needed once the last step is reached."""
        # disable automatic rerouting
        self._stop_tbt_worker()
        # automatic rerouting needs to be disabled to prevent rerouting
        # once the destination was reached
        self.destination_reached()

    def enabled(self):
        """Return if Turn by Turn navigation is enabled."""
        if self._route:
            return True
        else:
            return False

    def start_tbt(self, from_where='first'):
        """Start Turn-by-turn navigation."""

        # clean up any possible previous navigation data
        self._go_to_initial_state()

        # NOTE: turn and step are used interchangeably in the documentation
        m = self.m.get('route', None)
        if m:
            route = m.get_current_directions()
            if route:  # is the route nonempty ?
                self._route = route
                # get route in radians for automatic rerouting
                self.radiansRoute = route.get_points_lle_radians(drop_elevation=True)
                # start rerouting watch
                self._start_tbt_worker()

                # for some reason the combined distance does not account for the last step
                self._m_route_length = route.length

                # some statistics
                meters_per_sec_speed = self.get('metersPerSecSpeed', None)
                dt = m.route_lookup_duration
                self.log.info("route lookup took: %f s" % dt)
                if dt and meters_per_sec_speed:
                    dm = dt * meters_per_sec_speed
                    self.log.info("distance traveled during lookup: %f m" % dm)
                    # the duration of the road lookup and other variables are currently not used
                # in the heuristics but might be added later to make the heuristics more robust

                # now we decide if we use the closest turn, or the next one,
                # as we might be already past it and on our way to the next turn
                cs = self._get_closest_step()  # get geographically closest step
                pos = self.get('pos', None)  # get current position
                p_reached_dist = int(self.get('pointReachedDistance', 30))  # get the trigger distance
                next_turn_id = self._get_step_index(cs) + 1
                next_step = self._get_step(next_turn_id)
                # check if we have all the data needed for our heuristics
                self.log.info("trying to guess correct step to start navigation")
                if next_step and pos and p_reached_dist:
                    (lat, lon) = pos
                    (csLat, csLon) = cs.getLL()
                    (nsLat, nsLon) = next_step.getLL()
                    pos2next_step = geo.distance(lat, lon, nsLat, nsLon) * 1000
                    pos2current_step = geo.distance(lat, lon, csLat, csLon) * 1000
                    current_step2next_step = geo.distance(csLat, csLon, nsLat, nsLon) * 1000
                    #          self.log.debug("pos",(lat,lon))
                    #          self.log.debug("cs",(csLat,csLon))
                    #          self.log.debug("ns",(nsLat,nsLon))
                    self.log.debug("position to next turn: %f m" % pos2next_step)
                    self.log.debug("position to current turn: %f m" % pos2current_step)
                    self.log.debug("current turn to next turn: %f m" % current_step2next_step)
                    self.log.debug("turn reached trigger distance: %f m" % p_reached_dist)

                    if pos2current_step > p_reached_dist:
                        # this means we are out of the "capture circle" of the closest step

                        # what is more distant, the closest or the next step ?
                        if pos2next_step < current_step2next_step:
                            # we are mostly probably already past the closest step,
                            # so we switch to the next step at once
                            self.log.debug("already past closest turn, switching to next turn")
                            self.current_step = next_step
                            # we play the message for the next step,
                            # with current distance to this step,
                            # to assure there is some voice output immediately after
                            # getting a new route or rerouting"""
                            plaintextMessage = next_step.ssml_message
                            self._say_turn(plaintextMessage, pos2next_step)
                        else:
                            # we have probably not yet reached the closest step,
                            # so we start navigation from it
                            self.log.debug("closest turn not yet reached")
                            self.current_step = cs

                    else:
                        # we are inside the  "capture circle" of the closest step,
                        # this means the navigation will trigger the voice message by itself
                        # and correctly switch to next step
                        # -> no need to switch to next step from here
                        self.log.debug("inside reach distance of closest turn")
                        self.current_step = cs

                else:
                    # we dont have some of the data, that is needed to decide
                    # if we start the navigation from the closest step of from the step that is after it
                    # -> we just start from the closest step
                    self.log.debug("not enough data to decide, using closest turn")
                    self.current_step = cs
        self._do_navigation_update()  # run a first time navigation update
        self._location_watch_id = self.watch('locationUpdated', self.location_update_cb)
        self.log.info("started and ready")
        # trigger the navigation-started signal
        self.navigation_started()

    def stop_tbt(self):
        """Stop Turn-by-Turn navigation."""
        # remove location watch
        if self._location_watch_id:
            self.removeWatch(self._location_watch_id)
        # cleanup
        self._go_to_initial_state()
        self._stop_tbt_worker()
        self.log.info("stopped")
        self.navigation_stopped()

    def location_update_cb(self, key, newValue, oldValue):
        """Position changed, do a tbt navigation update."""
        # TODO: use a Signal for this ?
        if key == "locationUpdated":  # just to be sure
            self._do_navigation_update()
        else:
            self.log.error("invalid key: %r", key)

    def _do_navigation_update(self):
        """Do a navigation update."""
        # make sure there really are some steps
        if not self._route:
            self.log.error("no route")
            return
        pos = self.get('pos', None)
        if pos is None:
            self.log.error("skipping update, invalid position")
            return

        # get/compute/update necessary the values
        lat1, lon1 = pos
        lat2, lon2 = self.current_step.getLL()
        current_distance = geo.distance(lat1, lon1, lat2, lon2) * 1000  # km to m
        self._current_distance = current_distance  # update current distance

        # use some sane minimum distance
        distance = int(self.get('minAnnounceDistance', 100))

        # GHK: make distance speed-sensitive
        #
        # I came up with this formula after a lot of experimentation with
        # gnuplot.  The idea is to give the user some simple parameters to
        # adjust yet let him have a lot of control.  There are five
        # parameters in the equation:
        #
        # low_speed	Speed below which the pre-announcement time is constant.
        # low_time	Announcement time at and below lowSpeed.
        # high_speed	Speed above which the announcement time is constant.
        # high_time	Announcement time at and above highSpeed.
        # power	Exponential power used in the formula; good values are 0.5-5
        #
        # The speeds are in m/s.  Obviously highXXX must be greater than lowXXX.
        # If power is 1.0, announcement times increase linearly above lowSpeed.
        # If power < 1.0, times rise rapidly just above lowSpeed and more
        # gradually approaching highSpeed.  If power > 1.0, times rise
        # gradually at first and rapidly near highSpeed.  I like power > 1.0.
        #
        # The reasoning is that at high speeds you are probably on a
        # motorway/freeway and will need extra time to get into the proper
        # lane to take your exit.  That reasoning is pretty harmless on a
        # high-speed two-lane road, but it breaks down if you are stuck in
        # heavy traffic on a four-lane freeway (like in Los Angeles
        # where I live) because you might need quite a while to work your
        # way across the traffic even though you're creeping along.  But I
        # don't know a good way to detect whether you're on a multi-lane road,
        # I chose speed as an acceptable proxy.
        #
        # Regardless of speed, we always warn a certain distance ahead (see
        # "distance" above).  That distance comes from the value in the current
        # step of the directions.
        #
        # BTW, if you want to use gnuplot to play with the curves, try:
        # max(a,b) = a > b ? a : b
        # min(a,b) = a < b ? a : b
        # warn(x,t1,s1,t2,s2,p) = min(t2,(max(s1,x)-s1)**p*(t2-t1)/(s2-s1)**p+t1)
        # plot [0:160][0:] warn(x,10,50,60,100,2.0)
        #
        meters_per_sec_speed = self.get('metersPerSecSpeed', None)
        point_reached_distance = int(self.get('pointReachedDistance', 30))

        if meters_per_sec_speed:
            # check if we can miss the point by going too fast -> mps speed > point reached distance
            # also enlarge the rerouting threshold as it looks like it needs to be larger
            # when moving at high speed to prevent unnecessary rerouting
            if meters_per_sec_speed > point_reached_distance * 0.75:
                point_reached_distance = meters_per_sec_speed * 2
            #        self.log.debug("tbt: enlarging point reached distance to: %1.2f m due to large speed (%1.2f m/s)". (pointReachedDistance, metersPerSecSpeed)

            if meters_per_sec_speed > INCREASE_REROUTING_THRESHOLD_SPEED:
                self._rerouting_threshold_multiplier = REROUTING_THRESHOLD_MULTIPLIER
            else:
                self._rerouting_threshold_multiplier = 1.0

            # speed & time based triggering
            low_speed = float(self.get('minAnnounceSpeed', 13.89))
            high_speed = float(self.get('maxAnnounceSpeed', 27.78))
            high_speed = max(high_speed, low_speed + 0.1)
            low_time = int(self.get('minAnnounceTime', 10))
            high_time = int(self.get('maxAnnounceTime', 60))
            high_time = max(high_time, low_time)
            power = float(self.get('announcePower', 2.0))
            warn_time = (max(low_speed, meters_per_sec_speed) - low_speed) ** power \
                       * (high_time - low_time) / (high_speed - low_speed) ** power \
                       + low_time
            warn_time = min(high_time, warn_time)
            distance = max(distance, warn_time * meters_per_sec_speed)

            if self.get('debugTbT', False):
                self.log.debug("#####")
                self.log.debug("min/max announce time: %d/%d s", low_time, high_time)
                self.log.debug("trigger distance: %1.2f m (%1.2f s warning)", distance, distance / float(meters_per_sec_speed))
                self.log.debug("current distance: %1.2f m", current_distance)
                self.log.debug("current speed: %1.2f m/s (%1.2f km/h)", meters_per_sec_speed, meters_per_sec_speed * 3.6)
                self.log.debug("point reached distance: %f m", point_reached_distance)
                self.log.debug("1. triggered=%r, 1.5. triggered=%r, 2. triggered=%r",
                               self._espeak_first_trigger, self._espeak_first_and_half_trigger, self._espeak_second_trigger)
                if warn_time > 30:
                    self.log.debug("optional (20 s) trigger distance: %1.2f", 20.0 * meters_per_sec_speed)

            if current_distance <= point_reached_distance:
                # this means we reached the point"""
                if self._espeak_second_trigger is False:
                    self.log.debug("triggering espeak nr. 2")
                    # say the message without distance
                    plaintextMessage = self.current_step.ssml_message
                    # consider turn said even if it was skipped (ignore errors)
                    self._say_turn(plaintextMessage, 0)
                    self.current_step.visited = True  # mark this point as visited
                    self._espeak_first_trigger = True  # everything has been said, again :D
                    self._espeak_second_trigger = True  # everything has been said, again :D
                self.switch_to_next_step()  # switch to next step
            else:
                if current_distance <= distance:
                    # this means we reached an optimal distance for saying the message"""
                    if self._espeak_first_trigger is False:
                        self.log.debug("triggering espeak nr. 1")
                        plaintextMessage = self.current_step.ssml_message
                        if self._say_turn(plaintextMessage, current_distance):
                            self._espeak_first_trigger = True  # first message done
                if self._espeak_first_and_half_trigger is False and warn_time > 30:
                    if current_distance <= (20.0 * meters_per_sec_speed):
                        # in case that the warning time gets too big, add an intermediate warning at 20 seconds
                        # NOTE: this means it is said after the first trigger
                        plaintextMessage = self.current_step.ssml_message
                        if self._say_turn(plaintextMessage, current_distance):
                            self._espeak_first_and_half_trigger = True  # intermediate message done

            ## automatic rerouting ##

            # is automatic rerouting enabled from options
            # enabled == threshold that is not not None
            if self.automatic_rerouting_enabled:
                # rerouting is enabled only once the route is reached for the first time
                if self._on_route and not self._route_reached:
                    self._route_reached = True
                    self._automatic_reroute_counter = 0
                    self.log.info('route reached, rerouting enabled')

                # did the TBT worker detect that the rerouting threshold was reached ?
                if self._rerouting_conditions_met():
                    # test if enough consecutive divergence point were recorded
                    if self._rerouting_threshold_crossed_counter >= REROUTING_TRIGGER_COUNT:
                        # reset the routeReached override
                        self._override_route_reached = False
                        # trigger rerouting
                        self._reroute_auto()
                else:
                    # reset the counter
                    self._rerouting_threshold_crossed_counter = 0

    def _rerouting_conditions_met(self):
        return (self._route_reached or self._override_route_reached) and not self._on_route

    def _following_route(self):
        """Are we still following the route or is rerouting needed ?"""
        start1 = time.clock()
        pos = self.get('pos', None)
        proj = self.m.get('projection', None)
        if pos and proj:
            pLat, pLon = pos
            # we use Radians to get rid of radian conversion overhead for
            # the geographic distance computation method
            radians_ll = self.radiansRoute
            pLat = geo.radians(pLat)
            pLon = geo.radians(pLon)
            if len(radians_ll) == 0:
                self.log.error("Divergence: can't follow a zero point route")
                return False
            elif len(radians_ll) == 1:  # 1 point route
                aLat, aLon = radians_ll[0]
                min_distance = geo.distance_approx_radians(pLat, pLon, aLat, aLon)
            else:  # 2+ points route
                aLat, aLon = radians_ll[0]
                bLat, bLon = radians_ll[1]
                min_distance = geo.distance_point_to_line_radians(pLat, pLon, aLat, aLon, bLat, bLon)
                aLat, aLon = bLat, bLon
                for point in radians_ll[1:]:
                    bLat, bLon = point
                    dist = geo.distance_point_to_line_radians(pLat, pLon, aLat, aLon, bLat, bLon)
                    if dist < min_distance:
                        min_distance = dist
                    aLat, aLon = bLat, bLon
                # the multiplier tries to compensate for high speed movement
            threshold = float(
                self.get('reroutingThreshold', REROUTING_DEFAULT_THRESHOLD)) * self._rerouting_threshold_multiplier
            self.log.debug("Divergence from route: %1.2f/%1.2f m computed in %1.0f ms",
            min_distance * 1000, float(threshold), (1000 * (time.clock() - start1)))
            return min_distance * 1000 < threshold

    def _start_tbt_worker(self):
        with self._tbt_worker_lock:
            # reuse previous thread or start new one
            if self._tbt_worker_enabled:
                self.log.info("reusing TBT worker thread")
            else:
                self.log.info("starting new TBT worker thread")
                t = threads.ModRanaThread(name=constants.THREAD_TBT_WORKER,
                                          target=self._tbt_worker)
                threads.threadMgr.add(t)
                self._tbt_worker_enabled = True

    def _stop_tbt_worker(self):
        with self._tbt_worker_lock:
            self.log.info("stopping the TBT worker thread")
            self._tbt_worker_enabled = False

    def _tbt_worker(self):
        """This function runs in its own thread and checks if we are still following the route."""
        self.log.info("TBTWorker: started")
        # The _tbt_worker_enabled variable is needed as once the end of the route is reached
        # there will be a route set but further rerouting should not be performed.
        while True:
            with self._tbt_worker_lock:
                # Either tbt has been shut down (no route is set)
                # or rerouting is no longer needed.
                if not self._route or not self._tbt_worker_enabled:
                    self.log.info("TBTWorker: shutting down")
                    break

            # first make sure automatic rerouting is enabled
            # eq. reroutingThreshold != None
            if self.automatic_rerouting_enabled:
                # check if we are still following the route
                # self.log.debug('TBTWorker: checking divergence from route')
                self._on_route = self._following_route()
                if self._rerouting_conditions_met():
                    self.log.info('TBTWorker: divergence detected')
                    # switch to quick updates
                    for i in range(0, REROUTING_TRIGGER_COUNT + 1):
                        time.sleep(1)
                        onRoute = self._following_route()
                        if onRoute:  # divergence stopped
                            self._on_route = onRoute
                            self.log.info('TBTWorker: false alarm')
                            break
                        else:  # still diverging from current route
                            self._on_route = onRoute
                            # increase divergence counter
                            self._rerouting_threshold_crossed_counter += 1
                            self.log.debug('TBTWorker: increasing divergence counter (%d)',
                                           self._rerouting_threshold_crossed_counter)
            time.sleep(REROUTE_CHECK_INTERVAL / 1000.0)

    def shutdown(self):
        # cleanup
        self.stop_tbt()
