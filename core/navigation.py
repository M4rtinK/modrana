# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# A navigation hanling module.
#----------------------------------------------------------------------------
# Copyright 2018, Martin Kolman
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

from core import geo
from core import threads
from core import constants
from core import voice
from core.signal import Signal
import time
from threading import RLock

import logging
log = logging.getLogger("core.navigation")

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


class Turn(object):
    """A navigation turn.

    Basically a point where the direction of travel
    needs to be adjusted to keep following the current
    route.
    """

    def __init__(self, session, point, master_event):
        self._session = session
        self._point = point
        # Master events are used by the navigation session
        # to consider turns as reached, so the session can either
        # switch to the next turn or declare destination as reached.
        master_event.set_turn(self)
        self._master_event = master_event
        self._events = []
        self.master_event_triggered = Signal()

    @property
    def session(self):
        return self._session

    @property
    def point(self):
        return self._point

    @property
    def events(self):
        return self._events

    def add_event(self, event):
        event.set_turn(self)
        self._events.append(event)

    def prepare(self):
        """Prepare all events for running."""
        for event in self._events:
            event.prepare()

    def check_events(self):
        """Check if some events have been triggered.

        This is generally called periodically by the
        navigation session when current coordinates or
        some other important navigation session variables change.
        """
        if self._master_event.check_trigger():
            self.master_event_triggered()
        for event in self._events:
            event.check_trigger()

    def cleanup(self):
        """Cleanup data for all registered events."""
        self._master_event.cleanup()
        for event in self._events:
            event.cleanup()

class Trigger(object):
    """Base class for navigation event triggers.

    NOTE: We expect the trigger to be attached to
    navigation events, attached to turns, which
    are responsible for setting the point and session
    accordingly.
    """

    def __init__(self):
        self._event = None
        self._triggered = False

    @property
    def event(self):
        """The event this trigger is attached to."""
        return self._event

    def set_event(self, event):
        """Set "parent" navigation event."""
        self._event = event

    @property
    def triggered(self):
        """Report if the trigger has been triggered.

        This is set to True once the trigger condition is satisfied
        and remains True even after the condition might no longer
        satisfied.
        """
        return self._triggered

    def check_condition(self):
        if self._triggered:
            # we want this to evaluate as True only one
            return False
        elif self._do_check_condition():  # actually check the condition
            self._triggered = True
            return True
        else:
            return False

    def _do_check_condition(self):
        raise NotImplementedError

class DistanceTrigger(Trigger):
    """A distance based trigger.

    Triggered when the distance to a turn is less than
    the given distance number.
    """

    def __init__(self, distance):
        """
        :param distance: trigger distance in meters
        :param adjust_for_speed: adjust trigger distance for current

        About trigger distance adjustment

        This actually happened quite long ago when people first started using
        modRana in cars - users sometimes reported missed turn triggers even if
        they definitely went through the point. The cause turned out to be that
        their car was moving faster per second than was the size of the trigger circle.
        If they were going fast enough they could often "jump" ever a trigger circle
        between the navigation updates modRana generally does every second.

        To fix this modRana will compare current speed in meters per second and
        if it is close to the trigger circle size, it will increase the trigger circle
        size accordingly.
        """
        Trigger.__init__(self)
        self._distance = distance

    def _do_check_condition(self):
        # compute distance to turn from current position
        current_position = self.event.turn.session.current_position
        turn_point = self.event.turn.point
        # don't forget to convert the distance to meters
        distance = geo.distanceP2P(current_position, turn_point) * 1000
        current_speed = self.event.turn.session.current_speed  # in meters per second

        # Check if we can miss the point by going too fast -> m/s speed > point reached distance
        # and enlarge the trigger distance accordingly.
        if current_speed > self._distance * 0.75:
            trigger_distance = current_speed * 2
        else:
            trigger_distance = self._distance

        return distance <= trigger_distance

class TimeToPointTrigger(Trigger):
    """A time-to-point based trigger.

    Triggered when the time to a turn is less than
    the given time number (in seconds) at current
    average speed.
    """

    def __init__(self, time_to_point):
        """
        :param time_to_point: time to point in seconds
        """
        Trigger.__init__(self)
        self._time_to_point = time_to_point

    def _do_check_condition(self):
        # compute distance to turn from current position
        current_position = self.event.turn.session.current_position
        turn_point = self.event.turn.point
        # compute the distance and convert it to meters
        distance = geo.distanceP2P(current_position, turn_point) * 1000
        # divide the distance by average speed in meters per second
        average_speed = self.event.turn.session.average_speed
        current_time_to_point = distance / float(average_speed)
        return current_time_to_point <= self._time_to_point

class NavigationEvent(object):
    """A navigation event.

    A navigation event is a an event, generally triggered
    by distance from or time to some point that might
    require some sort of notification being shown to the user.

    For this purpose navigation events have triggers and actions
    which are run when the trigger fires.

    Navigation events are attached to Turns
    to play navigation messages when triggered.
    Turns are responsible for setting themselves
    as a turn for the given navigation event.
    """

    def __init__(self, trigger, actions):
        self._turn = None
        self._trigger = trigger
        self._trigger.set_event(self)
        self._actions = actions

    def set_turn(self, turn):
        """Set the turn corresponding to this navigation event."""
        self._turn = turn

    def check_trigger(self):
        """Check if any triggers fire in current session state."""
        if self._trigger.check_condition():
            for action in self._actions:
                action.run()
            return True
        else:
            return False

    def prepare(self):
        """Prepare all contained actions to be run."""
        for action in self._actions:
            action.prepare()

    def cleanup(self):
        """Cleanup all contained action."""
        for action in self._actions:
            action.cleanup()


class Action(object):
    """An action that can be performed."""

    def prepare(self):
        """Prepare the action to be ready to run.

        This generally means creating any caches or temporary data,
        such as voice message samples.
        """
        pass

    def run(self):
        """Perform the given action."""
        raise NotImplementedError

    def clean(self):
        """Clean any temporary resources associated with this action."""
        pass

class VoiceMessage(Action):
    """A navigation related voice message for the user."""

    def __init__(self, session, message):
        self._session = session
        self._message = message
        self._cleaned = False

    def prepare(self):
        # queue the voice message file to be generated
        self._session.voice_generator.make(self._message)

    def run(self):
        if self._cleaned:
            log.error("trying to play a cleaned voice message")
            return
        filename = self._session.voice_generator.get(self._message)
        if filename:
            self._session.play_voice_sample(filename)
        else:
            log.error("voice sample file missing for: %s" % self._message)

    def clean(self):
        self._session.voice_generator.clean_text(self._message)
        self._cleaned = True


class SwitchToNextTurn(Action):
    """An action used for switching to next turn.

    This action is generally attached to the maser event of all
    turns, except for the last one when the DestinationReached action is used.
    """

    def __init__(self, session):
        self._session = session

    def run(self):
        self._session.switch_to_next_turn()


class DestinationReached(Action):
    """An action used to indicate that the destination has been reached.

    This action is generally attached to the master event of the last turn
    instead of a SwitchToNextTurn action.

    """

    def __init__(self, session):
        self._session = session

    def run(self):
        # trigger the destination reached signal
        self._session.destination_reached()


class AdjustedTimeDistance(object):
    """Speed adjusted time and trigger distance."""

    def __init__(self):
        # some defaults
        self._min_announce_distance = 100
        self._point_reached_distance = 30
        self._min_announce_speed = 13.89
        self._max_announce_speed = 27.78
        self._min_announce_time = 10
        self._max_announce_time = 60
        self._announce_power = 2.0
        # debugging
        self._debug = False
        # results
        self._warn_time = None
        self._trigger_distance = None

    @property
    def min_announce_distance(self):
        return self._min_announce_distance

    @min_announce_distance.setter
    def min_announce_distance(self, distance):
        self._min_announce_distance = distance

    @property
    def point_reached_distance(self):
        return self._point_reached_distance

    @point_reached_distance.setter
    def point_reached_distance(self, distance):
        self._point_reached_distance = distance

    @property
    def min_announce_speed(self):
        return self._min_announce_speed

    @min_announce_speed.setter
    def min_announce_speed(self, speed):
        self._min_announce_speed = speed

    @property
    def max_announce_speed(self):
        return self._max_announce_speed

    @max_announce_speed.setter
    def max_announce_speed(self, speed):
        self._max_announce_speed = speed

    @property
    def min_announce_time(self):
        return self._min_announce_time

    @min_announce_time.setter
    def min_announce_time(self, speed):
        self._min_announce_time = speed

    @property
    def max_announce_time(self):
        return self._max_announce_time

    @max_announce_time.setter
    def max_announce_time(self, speed):
        self._max_announce_time = speed

    @property
    def announce_power(self):
        return self._announce_power

    @announce_power.setter
    def announce_power(self, power):
        self._announce_power = power

    @property
    def debug(self):
        return self._debug

    @debug.setter
    def debug(self, value):
        self._debug = value

    @property
    def warn_time(self):
        return self._warn_time

    @property
    def trigger_distance(self):
        return self._trigger_distance

    def update(self, current_speed):
        """Update speed based time/distance adjustment."""

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
        meters_per_sec_speed = current_speed
        point_reached_distance = self.point_reached_distance

        if meters_per_sec_speed:
            # check if we can miss the point by going too fast -> mps speed > point reached distance
            # also enlarge the rerouting threshold as it looks like it needs to be larger
            # when moving at high speed to prevent unnecessary rerouting
            if meters_per_sec_speed > point_reached_distance * 0.75:
                point_reached_distance = meters_per_sec_speed * 2
                if self.debug:
                    log.debug("enlarging point reached distance to: %1.2f m due to large speed (%1.2f m/s)",
                              point_reached_distance,
                              meters_per_sec_speed)

            # speed & time based triggering
            low_speed = self.min_announce_speed
            high_speed = self.max_announce_speed
            high_speed = max(high_speed, low_speed + 0.1)
            low_time = self.min_announce_time
            high_time = self.max_announce_time
            high_time = max(high_time, low_time)
            power = self.announce_power
            warn_time = (max(low_speed, meters_per_sec_speed) - low_speed) ** power \
                       * (high_time - low_time) / (high_speed - low_speed) ** power \
                       + low_time
            warn_time = min(high_time, warn_time)
            trigger_distance = max(self.min_announce_distance, warn_time * meters_per_sec_speed)

            if self.debug:
                log.debug("#####")
                log.debug("min/max announce time: %d/%d s", low_time, high_time)
                log.debug("trigger distance: %1.2f m (%1.2f s warning)", trigger_distance, trigger_distance / float(meters_per_sec_speed))
                log.debug("current speed: %1.2f m/s (%1.2f km/h)", meters_per_sec_speed, meters_per_sec_speed * 3.6)
                log.debug("point reached distance: %f m", point_reached_distance)
                if warn_time > 30:
                    log.debug("optional (20 s) trigger distance: %1.2f", 20.0 * meters_per_sec_speed)

            self._warn_time = warn_time
            self._trigger_distance = trigger_distance



class NavigationManager(object):
    """A top level navigation manager.

    A navigation manager manages and watches over individual navigation sessions.
    It handles such cases as sessions diverging from current route,
    in which case it triggers a rerouting event, which will generally
    result in the current navigation session being replaced
    by a new one based on the recomputed route.
    """

    def __init__(self, voice_generator):
        self._voice_generator = voice_generator
        self._session = None
        self._adjustment = AdjustedTimeDistance()
        self.rerouting_needed = Signal()

        # current position and speed
        self._current_position = None
        self._current_speed = 0

        # always needed voice messages
        # TODO: language ?
        self._rerouting_message = VoiceMessage(self, "rerouting")
        self._destination_reached_message = VoiceMessage(self, "You should be near the destination.")

        # signals
        self.navigation_started = Signal()
        self.navigation_stopped = Signal()
        self.current_turn_changed = Signal()
        self.rerouting_triggered = Signal()
        self.play_voice_sample = Signal()

    @property
    def adjustment(self):
        return self._adjustment

    def start_navigation(self, route):
        # cleanup previous session (if any)
        self.cleanup()
        # start new session
        self._session = NavigationSession(manager=self,
                                          voice_generator=self._voice_generator,
                                          route=route)
        # connect to session signals
        self._session.current_turn_changed.connect(self.current_turn_changed)
        self._session.destination_reached.connect(self._destination_reached_message.run)
        self._session.play_voice_sample.connect(self.play_voice_sample)
        # trigger the started signal
        self.navigation_started()

    def stop_navigation(self):
        self.cleanup()
        # trigger the stopped signal
        self.navigation_stopped()

    def cleanup(self):
        if self._session:
            # cleanup all temporary data held by the session
            self._session.cleanup()
            # disconnect all signals, just in case
            self._session.current_turn_changed.clear()
            self._session.destination_reached.clear()
            self._session.play_voice_sample.clear()
            # remove reference to the session
            self._session = None

    def update_position(self, current_position, current_speed):
        self._current_position = current_position
        self._current_speed = current_speed
        # check if we are still following the route

        # update the time/distance adjustment
        self.adjustment.update(current_speed=current_speed)

        # forward position update to the session (if any)
        if self._session:
            self._session.update_position(current_position, current_speed)

class NavigationSession(object):
    """A turn by turn navigation session."""

    def __init__(self, manager, voice_generator, route):
        # navigation manager
        self._manager = manager

        # position and speed
        self._current_position = None
        self._current_speed = 0
        self._average_speed = 0
        # voice
        self._voice_generator = voice_generator

        # route and turns
        self._route = route
        self._turns = self._generate_turns(self._route)
        self._current_turn_index = 0

        # rerouting
        self._rerouting_lock = RLock()
        self._route_reached = False
        self._following_route = False

        self._tbt_worker_lock = RLock()
        self._tbt_worker_enabled = False
        self._automatic_reroute_counter = 0  # counts consecutive automatic reroutes
        self._last_automatic_reroute_timestamp = time.time()
        # reroute even though the route was not yet reached (for special cases)
        self._override_route_reached = False
        # signals
        self.destination_reached = Signal()
        self.current_turn_changed = Signal()
        self.play_voice_sample = Signal()

    def _generate_turns(self, route):
        turns = []
        message_point_count = len(route.message_points)
        # some sanity checking
        if message_point_count == 0:
            log.error("route has no turns")
        elif message_point_count == 1:
            log.warning("route has a single turn")
        # generate the turns from message points
        point_index = 0
        for point in route.message_points:
            last_point = point_index == message_point_count - 1
            if last_point:
                switch_action = DestinationReached(session=self)
            else:
                switch_action = SwitchToNextTurn(session=self)
            turn_reached_message = VoiceMessage(session=self,
                                                message=point.description)

            master_event = NavigationEvent()


        # TODO: make this do things
        return turns

    @property
    def manager(self):
        return self._manager

    @property
    def route(self):
        return self._route


    def update_position(self, current_position, current_speed):
        self._current_position = current_position
        self._current_speed = current_speed


    @property
    def current_position(self):
        return self._current_position

    @property
    def current_speed(self):
        return self._current_speed

    @property
    def average_speed(self):
        return self._average_speed

    @property
    def voice_generator(self):
        return self._voice_generator

    def _get_turn_by_index(self, index):
        try:
            return self._turns[self._current_turn_index]
        except IndexError:
            return None

    @property
    def current_turn(self):
        return self._get_turn_by_index(self._current_turn_index)

    def switch_to_next_turn(self):
        if not self._turns:
            log.warning("can't switch to next turn - no turns")
            return
        next_turn_index = self._current_turn_index + 1
        if next_turn_index > (len(self._turns) - 1):
            # switch to the next turn
            self._current_turn_index = next_turn_index
            self.current_turn_changed(self.current_turn)
            # Schedule messages (or any other data) for the next turn to be generated.
            # As we always generate data for the next step right after switching,
            # we should generally always switch to to a step that has data already generated.
            next_turn = self._get_turn_by_index(self._current_turn_index + 1)
            if next_turn:
                next_turn.prepare()

            # As voice messages for the previous turn might still be playing
            # cleanup the turn before the previous one (if it exists).
            # This effectively means we will cache at most 3 turns worth of
            # voice messages, which should still be fine in general, but could
            # still be reduced if really needed.
            pre_previous_turn = self._get_turn_by_index(self._current_turn_index - 2)
            if pre_previous_turn:
                pre_previous_turn.cleanup()

    def cleanup(self):
        # cleanup all turns
        for turn in self._turns:
            turn.cleanup()

    def _reroute_auto(self):
        """This function is called when automatic rerouting is triggered."""

        # check time from last automatic reroute
        dt = time.time() - self._last_automatic_reroute_timestamp
        if dt >= AUTOMATIC_REROUTE_COUNTER_EXPIRATION_TIME:
            # reset the automatic reroute counter
            self._automatic_reroute_counter = 0
            log.debug('automatic reroute counter expired, clearing')

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
            log.debug('faking that route was reached to enable new rerouting')
            self._override_route_reached = True
        else:
            log.info('tbt: too many consecutive reroutes (%d),', self._automatic_reroute_counter)
            log.info('reach the route to enable automatic rerouting')
            log.info('or reroute manually')

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

    def _get_step(self, index):
        """Return steps for valid index, None otherwise."""
        max_index = self._max_step_index
        if index > max_index or index < -(max_index + 1):
            log.error("wrong turn index: %d, max index is: %d", index, max_index)
            return None
        else:
            return self._route.get_message_point_by_index(index)

    def _get_step_index(self, step):
        return self._route.get_message_point_index(step)

    def start_tbt(self, from_where='first'):
        """Start Turn-by-turn navigation."""

        # NOTE: turn and step are used interchangeably in the documentation
        route = self.route
        if route:
            route = route.get_current_directions()
            if route:  # is the route nonempty ?
                # start rerouting watch
                self._start_tbt_worker()

                # some statistics
                meters_per_sec_speed = self.current_speed
                dt = route.route_lookup_duration
                log.info("route lookup took: %f s" % dt)
                if dt and meters_per_sec_speed:
                    dm = dt * meters_per_sec_speed
                    log.info("distance traveled during lookup: %f m" % dm)
                    # the duration of the road lookup and other variables are currently not used
                # in the heuristics but might be added later to make the heuristics more robust

                # now we decide if we use the closest turn, or the next one,
                # as we might be already past it and on our way to the next turn
                cs = self._get_closest_step()  # get geographically closest step
                current_position = self.current_position  # get current position
                p_reached_dist = self.manager.adjustent.point_reached_distance  # get the trigger distance
                next_turn_id = self._get_step_index(cs) + 1
                next_step = self._get_step(next_turn_id)
                # check if we have all the data needed for our heuristics
                log.info("trying to guess correct step to start navigation")
                if next_step and current_position and p_reached_dist:
                    (lat, lon) = current_position
                    (csLat, csLon) = cs.getLL()
                    (nsLat, nsLon) = next_step.getLL()
                    pos2next_step = geo.distance(lat, lon, nsLat, nsLon) * 1000
                    pos2current_step = geo.distance(lat, lon, csLat, csLon) * 1000
                    current_step2next_step = geo.distance(csLat, csLon, nsLat, nsLon) * 1000
                    #          log.debug("pos",(lat,lon))
                    #          log.debug("cs",(csLat,csLon))
                    #          log.debug("ns",(nsLat,nsLon))
                    log.debug("position to next turn: %f m" % pos2next_step)
                    log.debug("position to current turn: %f m" % pos2current_step)
                    log.debug("current turn to next turn: %f m" % current_step2next_step)
                    log.debug("turn reached trigger distance: %f m" % p_reached_dist)

                    if pos2current_step > p_reached_dist:
                        # this means we are out of the "capture circle" of the closest step

                        # what is more distant, the closest or the next step ?
                        if pos2next_step < current_step2next_step:
                            # we are mostly probably already past the closest step,
                            # so we switch to the next step at once
                            log.debug("already past closest turn, switching to next turn")
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
                            log.debug("closest turn not yet reached")
                            self.current_step = cs

                    else:
                        # we are inside the  "capture circle" of the closest step,
                        # this means the navigation will trigger the voice message by itself
                        # and correctly switch to next step
                        # -> no need to switch to next step from here
                        log.debug("inside reach distance of closest turn")
                        self.current_step = cs

                else:
                    # we dont have some of the data, that is needed to decide
                    # if we start the navigation from the closest step of from the step that is after it
                    # -> we just start from the closest step
                    log.debug("not enough data to decide, using closest turn")
                    self.current_step = cs
        self._do_navigation_update()  # run a first time navigation update
        self._location_watch_id = self.watch('locationUpdated', self.location_update_cb)
        log.info("started and ready")
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
        log.info("stopped")
        self.navigation_stopped()

    def _do_navigation_update(self):
        """Do a navigation update."""
        # make sure there really are some steps
        if not self._route:
            log.error("no route")
            return
        pos = self.get('pos', None)
        if pos is None:
            log.error("skipping update, invalid position")
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
            #        log.debug("tbt: enlarging point reached distance to: %1.2f m due to large speed (%1.2f m/s)". (pointReachedDistance, metersPerSecSpeed)

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
                log.debug("#####")
                log.debug("min/max announce time: %d/%d s", low_time, high_time)
                log.debug("trigger distance: %1.2f m (%1.2f s warning)", distance, distance / float(meters_per_sec_speed))
                log.debug("current distance: %1.2f m", current_distance)
                log.debug("current speed: %1.2f m/s (%1.2f km/h)", meters_per_sec_speed, meters_per_sec_speed * 3.6)
                log.debug("point reached distance: %f m", point_reached_distance)
                log.debug("1. triggered=%r, 1.5. triggered=%r, 2. triggered=%r",
                               self._espeak_first_trigger, self._espeak_first_and_half_trigger, self._espeak_second_trigger)
                if warn_time > 30:
                    log.debug("optional (20 s) trigger distance: %1.2f", 20.0 * meters_per_sec_speed)

            if current_distance <= point_reached_distance:
                # this means we reached the point"""
                if self._espeak_second_trigger is False:
                    log.debug("triggering espeak nr. 2")
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
                        log.debug("triggering espeak nr. 1")
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
                    log.info('route reached, rerouting enabled')

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
                log.error("Divergence: can't follow a zero point route")
                return False
            elif len(radians_ll) == 1:  # 1 point route
                aLat, aLon = radians_ll[0]
                min_distance = geo.distanceApproxRadians(pLat, pLon, aLat, aLon)
            else:  # 2+ points route
                aLat, aLon = radians_ll[0]
                bLat, bLon = radians_ll[1]
                min_distance = geo.distancePointToLineRadians(pLat, pLon, aLat, aLon, bLat, bLon)
                aLat, aLon = bLat, bLon
                for point in radians_ll[1:]:
                    bLat, bLon = point
                    dist = geo.distancePointToLineRadians(pLat, pLon, aLat, aLon, bLat, bLon)
                    if dist < min_distance:
                        min_distance = dist
                    aLat, aLon = bLat, bLon
                # the multiplier tries to compensate for high speed movement
            threshold = float(
                self.get('reroutingThreshold', REROUTING_DEFAULT_THRESHOLD)) * self._rerouting_threshold_multiplier
            log.debug("Divergence from route: %1.2f/%1.2f m computed in %1.0f ms",
            min_distance * 1000, float(threshold), (1000 * (time.clock() - start1)))
            return min_distance * 1000 < threshold

    def _start_tbt_worker(self):
        with self._tbt_worker_lock:
            # reuse previous thread or start new one
            if self._tbt_worker_enabled:
                log.info("reusing TBT worker thread")
            else:
                log.info("starting new TBT worker thread")
                t = threads.ModRanaThread(name=constants.THREAD_TBT_WORKER,
                                          target=self._tbt_worker)
                threads.threadMgr.add(t)
                self._tbt_worker_enabled = True

    def _stop_tbt_worker(self):
        with self._tbt_worker_lock:
            log.info("stopping the TBT worker thread")
            self._tbt_worker_enabled = False

    def _tbt_worker(self):
        """This function runs in its own thread and checks if we are still following the route."""
        log.info("TBTWorker: started")
        # The _tbt_worker_enabled variable is needed as once the end of the route is reached
        # there will be a route set but further rerouting should not be performed.
        while True:
            with self._tbt_worker_lock:
                # Either tbt has been shut down (no route is set)
                # or rerouting is no longer needed.
                if not self._route or not self._tbt_worker_enabled:
                    log.info("TBTWorker: shutting down")
                    break

            # first make sure automatic rerouting is enabled
            # eq. reroutingThreshold != None
            if self.automatic_rerouting_enabled:
                # check if we are still following the route
                # log.debug('TBTWorker: checking divergence from route')
                self._on_route = self._following_route()
                if self._rerouting_conditions_met():
                    log.info('TBTWorker: divergence detected')
                    # switch to quick updates
                    for i in range(0, REROUTING_TRIGGER_COUNT + 1):
                        time.sleep(1)
                        onRoute = self._following_route()
                        if onRoute:  # divergence stopped
                            self._on_route = onRoute
                            log.info('TBTWorker: false alarm')
                            break
                        else:  # still diverging from current route
                            self._on_route = onRoute
                            # increase divergence counter
                            self._rerouting_threshold_crossed_counter += 1
                            log.debug('TBTWorker: increasing divergence counter (%d)',
                                           self._rerouting_threshold_crossed_counter)
            time.sleep(REROUTE_CHECK_INTERVAL / 1000.0)
