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
from modules.base_module import RanaModule
from core import geo
from threading import Thread
import math
import time


import instructions_generator

REROUTE_CHECK_INTERVAL = 5000 # in ms
#in m/s, about 46 km/h - if this speed is reached, the rerouting threshold is multiplied
# by REROUTING_THRESHOLD_MULTIPLIER
INCREASE_REROUTING_THRESHOLD_SPEED = 20
REROUTING_DEFAULT_THRESHOLD = 30
# not enabled at the moment - needs more field testing
REROUTING_THRESHOLD_MULTIPLIER = 1.0
# how many times needs the threshold be crossed to
# trigger rerouting
REROUTING_TRIGGER_COUNT = 3

MAX_CONSECUTIVE_AUTOMATIC_REROUTES = 3
AUTOMATIC_REROUTE_COUNTER_EXPIRATION_TIME = 600 # in seconds

# only import GKT libs if GTK GUI is used
from core import gs
if gs.GUIString == "GTK":
  import pango
  import pangocairo

def getModule(m,d,i):
  return turnByTurn(m,d,i)

class turnByTurn(RanaModule):
  """A turn by turn navigation module."""
  
  def __init__(self, m, d, i):
    RanaModule.__init__(self, m, d, i)
    gui = self.modrana.gui
    # initial colors
    self.navigationBoxBackground = (0,0,1,0.3) # very transparent blue
    self.navigationBoxText = (1,1,1,1) # non-transparent white
    self.TBTWorker = None
    self.TBTWorkerEnabled = False
    self.goToInitialState()
    self.automaticRerouteCounter = 0 # counts consecutive automatic reroutes
    self.lastAutomaticRerouteTimestamp = time.time()
    # reroute even though the route was not yet reached (for special cases)
    self.overrideRouteReached = False

  def goToInitialState(self):
    """restore initial state"""
    self.route = None
    self.currentStepIndex = 0
    self.currentStepIndicator = None
    self.espeakFirstAndHalfTrigger = False
    self.espeakFirstTrigger = False
    self.espeakSecondTrigger = False
    self.currentDistance = None
    self.currentStep = None
    self.navigationBoxHidden = False
    self.mRouteLength = 0
    self.locationWatchID = None
    self.onRoute = False
    #rerouting is enabled once the route is reached for the first time
    self.routeReached = False
    self.reroutingThresholdMultiplier = 1.0
    self.reroutingThresholdCrossedCounter = 0

  def firstTime(self):
    icons = self.m.get('icons', None)
    if icons:
      icons.subscribeColorInfo(self,self.colorsChangedCallback)

  def colorsChangedCallback(self,colors):
    self.navigationBoxBackground = colors['navigation_box_background'].getCairoColor()
    self.navigationBoxText = colors['navigation_box_text'].getCairoColor()
    
  def handleMessage(self, message, type, args):
    if message == 'start':
      if type == 'ms':
        fromWhere = args
        self.startTBT(fromWhere)
    elif message == 'stop':
      self.stopTBT()
    elif message == 'reroute': # manual rerouting
      # reset automatic reroute counter
      self.automaticRerouteCounter = 0
      self._reroute()
    elif message == "toggleBoxHiding":
      print("turnByTurn: toggling navigation box visibility")
      self.navigationBoxHidden = not self.navigationBoxHidden
    elif message == "switchToPreviousTurn":
      self.switchToPreviousStep()
    elif message == "switchToNextTurn":
      self.switchToNextStep()
    elif message == "showMessageInsideNotification":
      currentStep = self.getCurrentStep()
      if currentStep:
        message = "<i>turn description:</i>\n%s" % currentStep.getMessage()
        if self.dmod.hasNotificationSupport():
          self.dmod.notify(message,7000)
      #TODO: add support for modRana notifications once they support line wrapping

  def _rerouteAuto(self):
    """this function is called when automatic rerouting is triggered"""

    # check time from last automatic reroute
    dt = time.time() - self.lastAutomaticRerouteTimestamp
    if dt >= AUTOMATIC_REROUTE_COUNTER_EXPIRATION_TIME:
      # reset the automatic reroute counter
      self.automaticRerouteCounter = 0
      print('tbt: automatic reroute counter expired, clearing')

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

    if self.automaticRerouteCounter < MAX_CONSECUTIVE_AUTOMATIC_REROUTES:
      print('tbt: faking that route was reached to enable new rerouting')
      self.overrideRouteReached = True
    else:
      print('tbt: too many consecutive reroutes (%d),' % self.automaticRerouteCounter)
      print('reach the route to enable automatic rerouting')
      print('or reroute manually')

    # increment the automatic reroute counter & update the timestamp
    self.automaticRerouteCounter+=1
    self.lastAutomaticRerouteTimestamp = time.time()

    # trigger rerouting
    self._reroute()

  def _reroute(self):
    # 1. say rerouting is in progress
    voiceMessage = "rerouting"
    voice = self.m.get('voice', None)
    if voice:
      voice.say(voiceMessage, "en") # make sure rerouting said with english voice
    time.sleep(2) #TODO: improve this
    # 2. get a new route from current position to destination
    self.sendMessage("ms:route:reroute:fromPosToDest")
    # 3. restart routing for to this new route from the closest point
    self.sendMessage("ms:turnByTurn:start:closest")

  def drawMapOverlay(self,cr):
      if self.route:
        # get current step
        currentStep = self.getCurrentStep()
        proj = self.m.get('projection', None)
        # draw the current step indicator circle
        if currentStep and proj:
          (lat, lon) = currentStep.getLL()
          (pointX, pointY) = proj.ll2xy(lat, lon)
          cr.set_source_rgb(1, 0, 0)
          cr.set_line_width(4)
          cr.arc(pointX, pointY, 12, 0, 2.0 * math.pi)
          cr.stroke()
          cr.fill()

  def drawScreenOverlay(self, cr):
    if self.route: # is there something relevant to draw ?
    
      # get current step
      currentStep = self.getCurrentStep()

      # draw the routing message box

      # we need to have the viewport available
      vport = self.get('viewport', None)
      menus = self.m.get('menu', None)
      if vport and menus:
        (sx,sy,w,h) = vport
        (bx,by,bw,bh) = (w*0.15,h*0.20,w*0.7,h*0.4)
        buttonStripOffset = 0.25 * bh

        # construct parametric background for the cairo drawn buttons
        background="generic:;0;;1;5;0"
        
        if self.navigationBoxHidden:
          # * show button
          showButtonWidth = bw * 0.2
          # the show button uses custom parameters
          parametricIconName="center:show;0.1>%s" % background
          menus.drawButton(cr, bx+(bw-showButtonWidth), by, showButtonWidth, buttonStripOffset, "", parametricIconName, "turnByTurn:toggleBoxHiding")
  
        else:
          # draw the info-box background
          cr.set_source_rgba(*self.navigationBoxBackground)
          cr.rectangle(bx,by+buttonStripOffset,bw,bh-buttonStripOffset)
          cr.fill()
          
          # create a layout for our drawing area
          pg = pangocairo.CairoContext(cr)
          layout = pg.create_layout()

          # get the current turn message
          message = currentStep.getMessage()
      
          # display current distance to the next point & other unit conversions
          units = self.m.get('units', None)
          if units and self.currentDistance:
            distString = units.m2CurrentUnitString(self.currentDistance,1,True)
            if currentStep.getDistanceFromStart():
              currentDistString = units.m2CurrentUnitString(currentStep.getDistanceFromStart(),1,True)
            else:
              currentDistString = "?"
            routeLengthString = units.m2CurrentUnitString(self.mRouteLength,1,True)
          else:
            distString = ""
            currentDistString = ""
            routeLengthString = ""

          # TODO: find why there needs to be a newline on the end
          message = "%s : %s\n" % (distString, message)

          border = min(bw/50.0,bh/50.0)
          # compute how much space is actually available for the text
          usableWidth = bw-2*border
          usableHeight = bh-6*border-buttonStripOffset
          layout.set_width(int(usableWidth*pango.SCALE))
          layout.set_wrap(pango.WRAP_WORD)
          layout.set_markup(message)
          layout.set_font_description(pango.FontDescription("Sans Serif 24")) #TODO: custom font size ?
          (lw,lh) = layout.get_size()
          if lw == 0 or lh == 0:
            # no need to draw a zero area layout
            return

          # get coordinates for the area available for text
          ulX,ulY = (bx+border,by+border+buttonStripOffset)
          cr.move_to(ulX,ulY)
          cr.save()
          if lh > usableHeight: # is the rendered text larger than the usable area ?
            clipHeight = 0
            # find last completely visible line
            cut = False
            for id in range(0,layout.get_line_count()-1):
              lineHeight = layout.get_line(id).get_pixel_extents()[1][3]
              if clipHeight + lineHeight <= usableHeight:
                clipHeight = clipHeight + lineHeight
              else:
                cut = True # signalize we cut off some lines
                break
            
            textEndY = by+border+clipHeight+buttonStripOffset

            if cut:
              """ notify the user that a part of the text was cut,
                          by drawing a red line and a scissors icon"""
              # draw the red line
              cr.set_source_rgb(1,0,0)
              cr.set_line_width(bh*0.01)
              cr.move_to(bx,textEndY)
              cr.line_to(bx+bw,textEndY)
              cr.stroke()
              # draw the scissors icon
              cutSide = bw/10
              menus.drawButton(cr, bx+bw, textEndY-cutSide/2.0, cutSide, cutSide, "", "center:scissors_right;0>%s" % background, "turnByTurn:showMessageInsideNotification")
              #TODO: show the whole message in a notifications after clicking the scissors
              # (this needs line wrapping support in modRana notifications)

            # clip out the overflowing part of the text
            cr.rectangle(ulX,ulY,usableWidth,clipHeight)
            cr.translate(ulX,ulY)
            cr.clip()

          cr.set_source_rgba(*self.navigationBoxText)
          pg.show_layout(layout)
          cr.restore()

          # use the bottom of the infobox to display info
          (bottomX,bottomY) = (bx, by+bh-6*border)
          if self.routeReached and self._automaticReroutingEnabled():
            arString = "automatic rerouting enabled"
          else:
            arString ="tap this box to reroute"
          note = "%s/%s, %d/%d   <sub> %s</sub>" % (currentDistString, routeLengthString, self.currentStepIndex+1, self.getMaxStepIndex()+1, arString)
          menus.drawText(cr, "%s" % note, bottomX, bottomY, bw, 6*border, 0, rgbaColor=self.navigationBoxText)
          # make clickable
          clickHandler = self.m.get('clickHandler', None)
          if clickHandler:
            action = "turnByTurn:reroute"
            clickHandler.registerXYWH(bx, by+buttonStripOffset , bw, bh-buttonStripOffset, action)

          # draw the button strip
          hideButtonWidth = bw * 0.2
          switchButtonWidth = bw * 0.4

          # * previous turn button
          menus.drawButton(cr, bx, by, switchButtonWidth, buttonStripOffset, "", "center:less;0.1>%s" % background, "turnByTurn:switchToPreviousTurn")
          # * next turn button
          menus.drawButton(cr, bx+switchButtonWidth, by, switchButtonWidth, buttonStripOffset, "", "center:more;0.1>%s" % background, "turnByTurn:switchToNextTurn")
          # * hide button
          menus.drawButton(cr, bx+2*switchButtonWidth, by, hideButtonWidth, buttonStripOffset, "", "center:hide;0.1>%s" % background, "turnByTurn:toggleBoxHiding")

  def _automaticReroutingEnabled(self):
    return self.get('reroutingThreshold', REROUTING_DEFAULT_THRESHOLD)

  def sayTurn(self,message,distanceInMeters,forceLanguageCode=False):
    """say a text-to-speech message about a turn
       this basically wraps the simple say method from voice and adds some more information,
       like current distance to the turn
       """
    voice = self.m.get('voice', None)
    units = self.m.get('units', None)

    if voice and units:
      (distString, short, long) = units.humanRound(distanceInMeters)

      if distString == "0":
        distString = ""
      else:
        distString = '<p xml:lang="en">in <emphasis level="strong">'+ distString + ' ' + long + '</emphasis></p><br>'
        # TODO: language specific distance strings
      text = distString + message

#      """ the message can contain unicode, this might cause an exception when printing it
#      in some systems (SHR-u on Neo, for example)"""
#      try:
#        print("saying: %s" % text)
#        pass
#      except UnicodeEncodeError:
#        print("voice: printing the current message to stdout failed do to unicode conversion error")

      if forceLanguageCode:
        espeakLanguageCode = forceLanguageCode
      else:
        # the espeak language code is the first part of this whitespace delimited string
        espeakLanguageCode = self.get('directionsLanguage', 'en en').split(" ")[0]
      return voice.say(text,espeakLanguageCode)

  def getMaxStepIndex(self):
    return self.route.getMessagePointCount() - 1

  def getStartingStep(self, which='first'):
    if self.route:
      if which == 'first':
        return self.getStep(0)
      if which == 'closest':
        return self.getClosestStep()

  def getClosestStep(self):
    """get the geographically closest step"""
    proj = self.m.get('projection', None) # we also need the projection module
    pos = self.get('pos', None) # and current position
    if pos and proj:
      (lat1,lon1) = pos
      tempSteps = self.route.getMessagePoints()
      for step in tempSteps:
        (lat2, lon2) = step.getLL()
        step.setCurrentDistance = geo.distance(lat1,lon1,lat2,lon2)*1000 # km to m
      closestStep = sorted(tempSteps, key=lambda x: x.getCurrentDistance())[0]

      return closestStep

  def getStep(self, index):
    """return steps for valid index, None otherwise"""
    maxIndex = self.getMaxStepIndex()
    if index > maxIndex or index < -(maxIndex+1):
      print("turnByTurn: wrong turn index: %d, max index is: %d" % (index, maxIndex))
      return None
    else:
      return self.route.getMessagePointByID(index)

  def setStepAsCurrent(self, step):
    """set a given step as current step"""
    id = self.route.getMessagePointID(step)
    self._setCurrentStepIndex(id)

  def getCurrentStep(self):
    """return current step"""
    return self.route.getMessagePointByID(self.currentStepIndex)

  def getStepID(self, step):
    return self.route.getMessagePointID(step)

  def getCurrentStepVisitStatus(self):
    """report visit status for  current step"""
    return self.getCurrentStep().getVisited()

  def markCurrentStepAsVisited(self):
    """mark current step as visited"""
    self.getCurrentStep().setVisited(True)

  def switchToPreviousStep(self):
    """switch to previous step and clean up"""
    nextIndex = self.currentStepIndex - 1
    if nextIndex >= 0:
      self._setCurrentStepIndex(nextIndex)
      self.espeakFirstTrigger = False
      self.espeakSecondTrigger = False
      print("tbt: switching to previous step")
    else:
      print("tbt: previous step reached")

  def switchToNextStep(self):
    """switch to next step and clean up"""
    maxIndex = self.getMaxStepIndex()
    nextIndex = self.currentStepIndex + 1
    if nextIndex <= maxIndex:
      self._setCurrentStepIndex(nextIndex)
      self.espeakFirstAndHalfTrigger = False
      self.espeakFirstTrigger = False
      self.espeakSecondTrigger = False
      print("tbt: switching to next step")
    else:
      print("tbt: last step reached")
      self._lastStepReached()

  def _lastStepReached(self):
    """handle all tasks that are needed once the last step is reached"""
    #disable automatic rerouting
    self._stopTBTWorker()
    # automatic rerouting needs to be disabled to prevent rerouting
    # once the destination was reached

  def _setCurrentStepIndex(self, index):
    self.currentStepIndex = index
    self._doNavigationUpdate()

  def enabled(self):
    """return True if enabled, false otherwise"""
    if self.route:
      return True
    else:
      return False

  def startTBT(self, fromWhere='first'):
    """start Turn-by-turn navigation"""

    # clean up any possible previous navigation data
    self.goToInitialState()

    """NOTE: turn and step are used interchangeably in the documentation"""
    m = self.m.get('route', None)
    if m:
      (route,routeRequestSentTimestamp) = m.getCurrentDirections()
      if route: # is the route nonempty ?
        self.route = route
        # get route in radians for automatic rerouting
        self.radiansRoute = route.getPointsLLERadians(dropElevation=True)
        # start rerouting watch
        self._startTBTWorker()

        # show the warning message
        self.sendMessage('ml:notification:m:use at own risk, watch for cliffs, etc.;3')
        # for some reason the combined distance does not account for the last step
        self.mRouteLength = route.getLength()

        # some statistics
        metersPerSecSpeed = self.get('metersPerSecSpeed', None)
        dt = time.time() - routeRequestSentTimestamp
        print("turnByTurn: route lookup took: %f s" % dt)
        if dt and metersPerSecSpeed:
          dm = dt * metersPerSecSpeed
          print("distance traveled during lookup: %f m" % dm)
        """the duration of the road lookup and other variables are currently not used
        in the heuristics but might be added later to make the heuristics more robust"""


        """now we decide if we use the closest turn, or the next one,
        as we might be already past it and on our way to the next turn"""
        cs = self.getClosestStep() # get geographically closest step
        pos = self.get('pos', None) # get current position
        pReachedDist = int(self.get('pointReachedDistance', 30)) # get the trigger distance
        nextTurnId = self.getStepID(cs) + 1
        nextStep = self.getStep(nextTurnId)
        # check if we have all the data needed for our heuristics
        print("tbt: trying to guess correct step to start navigation")
        if nextStep and pos and pReachedDist:
          (lat,lon) = pos
          (csLat,csLon) = cs.getLL()
          (nsLat,nsLon) = nextStep.getLL()
          pos2nextStep = geo.distance(lat,lon,nsLat,nsLon)*1000
          pos2currentStep = geo.distance(lat,lon,csLat,csLon)*1000
          currentStep2nextStep = geo.distance(csLat,csLon,nsLat,nsLon)*1000
#          print "pos",(lat,lon)
#          print "cs",(csLat,csLon)
#          print "ns",(nsLat,nsLon)
          print("position to next turn: %f m" % pos2nextStep)
          print("position to current turn: %f m" % pos2currentStep)
          print("current turn to next turn: %f m" % currentStep2nextStep)
          print("turn reached trigger distance: %f m" % pReachedDist)

          if pos2currentStep > pReachedDist:
            #this means we are out of the "capture circle" of the closest step

            # what is more distant, the closest or the next step ?
            if pos2nextStep < currentStep2nextStep:
              # we are mostly probably already past the closest step,
              # so we switch to the next step at once
              print("tbt: already past closest turn, switching to next turn")
              self.setStepAsCurrent(nextStep)
              """we play the message for the next step,
              with current distance to this step,
              to assure there is some voice output immediately after
              getting a new route or rerouting"""
              plaintextMessage = nextStep.getSSMLMessage()
              self.sayTurn(plaintextMessage, pos2nextStep)
            else:
              # we have probably not yet reached the closest step,
              # so we start navigation from it
              print("tbt: closest turn not yet reached")
              self.setStepAsCurrent(cs)

          else:
            """we are inside the  "capture circle" of the closest step,
            this means the navigation will trigger the voice message by itself
            and correctly switch to next step
            -> no need to switch to next step from here"""
            print("tbt: inside reach distance of closest turn")
            self.setStepAsCurrent(cs)

        else:
          """we dont have some of the data, that is needed to decide
          if we start the navigation from the closest step of from the step that is after it
          -> we just start from the closest step"""
          print("tbt: not enough data to decide, using closest turn")
          self.setStepAsCurrent(cs)
    self._doNavigationUpdate() # run a first time navigation update
    self.locationWatchID = self.watch('locationUpdated', self.locationUpdateCB)
    print("tbt: started")
      
  def stopTBT(self):
    """stop Turn-by-turn navigation"""
    # remove location watch
    if self.locationWatchID:
      self.removeWatch(self.locationWatchID)
    # cleanup
    self.goToInitialState()
    self._stopTBTWorker()
    print("tbt: stopped")

  def locationUpdateCB(self, key, newValue, oldValue):
    """position changed, do a tbt navigation update"""
    if key == "locationUpdated": # just to be sure
      self._doNavigationUpdate()
    else:
      print("tbt: invalid key: %r" % key)

  def _doNavigationUpdate(self):
    """do a navigation update"""
    # make sure there really are some steps
    if not self.route:
      print("tbt: error no route")
      return
    pos = self.get('pos', None)
    if pos is None:
      print("tbt: skipping update, invalid position")
      return

    # get/compute/update necessary the values
    (lat1,lon1) = pos
    currentStep = self.getCurrentStep()
    lat2, lon2 = currentStep.getLL()
    currentDistance = geo.distance(lat1,lon1,lat2,lon2)*1000 # km to m
    self.currentDistance = currentDistance # update current distance

    # use some sane minimum distance
    distance = int(self.get('minAnnounceDistance',100))

    # GHK: make distance speed-sensitive
    #
    # I came up with this formula after a lot of experimentation with
    # gnuplot.  The idea is to give the user some simple parameters to
    # adjust yet let him have a lot of control.  There are five
    # parameters in the equation:
    #
    # lowSpeed	Speed below which the pre-announcement time is constant.
    # lowTime	Announcement time at and below lowSpeed.
    # highSpeed	Speed above which the announcement time is constant.
    # highTime	Announcement time at and above highSpeed.
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
    metersPerSecSpeed = self.get('metersPerSecSpeed', None)
    pointReachedDistance = int(self.get('pointReachedDistance', 30))

    if metersPerSecSpeed:
      # check if we can miss the point by going too fast -> mps speed > point reached distance
      # also enlarge the rerouting threshold as it looks like it needs to be larger
      # when moving at high speed to prevent unnecessary rerouting
      if metersPerSecSpeed > pointReachedDistance*0.75:
        pointReachedDistance = metersPerSecSpeed*2
#        print("tbt: enlarging point reached distance to: %1.2f m due to large speed (%1.2f m/s)" % (pointReachedDistance, metersPerSecSpeed))

      if metersPerSecSpeed > INCREASE_REROUTING_THRESHOLD_SPEED:
        self.reroutingThresholdMultiplier = REROUTING_THRESHOLD_MULTIPLIER
      else:
        self.reroutingThresholdMultiplier = 1.0

      # speed & time based triggering
      lowSpeed = float(self.get('minAnnounceSpeed', 13.89))
      highSpeed = float(self.get('maxAnnounceSpeed', 27.78))
      highSpeed = max(highSpeed, lowSpeed + 0.1)
      lowTime = int(self.get('minAnnounceTime', 10))
      highTime = int(self.get('maxAnnounceTime', 60))
      highTime = max(highTime, lowTime)
      power = float(self.get('announcePower', 2.0))
      warnTime = (max(lowSpeed, metersPerSecSpeed) - lowSpeed)**power \
        * (highTime - lowTime) / (highSpeed - lowSpeed)**power \
        + lowTime
      warnTime = min(highTime, warnTime)
      distance = max(distance, warnTime * metersPerSecSpeed)

      if self.get('debugTbT', False):
        print("#####")
        print("min/max announce time: %d/%d s" % (lowTime, highTime))
        print("trigger distance: %1.2f m (%1.2f s warning)" % (distance, distance/float(metersPerSecSpeed)))
        print("current distance: %1.2f m" % currentDistance)
        print("current speed: %1.2f m/s (%1.2f km/h)" % (metersPerSecSpeed, metersPerSecSpeed*3.6))
        print("point reached distance: %f m" % pointReachedDistance)
        print("1. triggered=%r, 1.5. triggered=%r, 2. triggered=%r" % (self.espeakFirstTrigger, self.espeakFirstAndHalfTrigger, self.espeakSecondTrigger))
        if warnTime > 30:
          print("optional (20 s) trigger distance: %1.2f" % (20.0*metersPerSecSpeed))

      if currentDistance <= pointReachedDistance:
        """this means we reached the point"""
        if self.espeakSecondTrigger == False:
          print("triggering espeak nr. 2")
          # say the message without distance
          plaintextMessage = currentStep.getSSMLMessage()
          # consider turn said even if it was skipped (ignore errors)
          self.sayTurn(plaintextMessage, 0)
          self.markCurrentStepAsVisited() # mark this point as visited
          self.espeakFirstTrigger = True # everything has been said, again :D
          self.espeakSecondTrigger = True # everything has been said, again :D
        self.switchToNextStep() # switch to next step
      else:
        if currentDistance <= distance:
          """this means we reached an optimal distance for saying the message"""
          if self.espeakFirstTrigger == False:
            print("triggering espeak nr. 1")
            plaintextMessage = currentStep.getSSMLMessage()
            if self.sayTurn(plaintextMessage, currentDistance):
              self.espeakFirstTrigger = True # first message done
        if self.espeakFirstAndHalfTrigger == False and warnTime > 30:
          if currentDistance <= (20.0*metersPerSecSpeed):
            """in case that the warning time gets too big, add an intermediate warning at 20 seconds
            NOTE: this means it is said after the first trigger
            """
            plaintextMessage = currentStep.getSSMLMessage()
            if self.sayTurn(plaintextMessage, currentDistance):
              self.espeakFirstAndHalfTrigger = True # intermediate message done

      ## automatic rerouting ##

      # is automatic rerouting enabled from options
      # enabled == threshold that is not not None
      if self._automaticReroutingEnabled():
        # rerouting is enabled only once the route is reached for the first time
        if self.onRoute and not self.routeReached:
          self.routeReached = True
          self.automaticRerouteCounter = 0
          print('tbt: route reached, rerouting enabled')

        # did the TBT worker detect that the rerouting threshold was reached ?
        if self._reroutingConditionsMet():
          # test if enough consecutive divergence point were recorded
          if self.reroutingThresholdCrossedCounter >= REROUTING_TRIGGER_COUNT:
            # reset the routeReached override
            self.overrideRouteReached = False
            # trigger rerouting
            self._rerouteAuto()
        else:
          # reset the counter
          self.reroutingThresholdCrossedCounter = 0

  def _reroutingConditionsMet(self):
    return (self.routeReached or self.overrideRouteReached) and not self.onRoute

  def _followingRoute(self):
    """are we still following the route or is rerouting needed"""
    start1 = time.clock()
    pos = self.get('pos', None)
    proj = self.m.get('projection', None)
    if pos and proj:
      pLat, pLon = pos
      # we use Radians to get rid of radian conversion overhead for
      # the geographic distance computation method
      radiansLL = self.radiansRoute
      pLat = geo.radians(pLat)
      pLon = geo.radians(pLon)
      if len(radiansLL) == 0:
        print("Divergence: can't follow a zero point route")
        return False
      elif len(radiansLL) == 1: # 1 point route
        aLat, aLon = radiansLL[0]
        minDistance = geo.distanceApproxRadians(pLat, pLon, aLat, aLon)
      else: # 2+ points route
        aLat, aLon = radiansLL[0]
        bLat, bLon = radiansLL[1]
        minDistance = geo.distancePointToLineRadians(pLat, pLon, aLat, aLon, bLat, bLon)
        aLat, aLon = bLat, bLon
        for point in radiansLL[1:]:
          bLat, bLon = point
          dist = geo.distancePointToLineRadians(pLat, pLon, aLat, aLon, bLat, bLon)
          if dist < minDistance:
            minDistance = dist
          aLat, aLon = bLat, bLon
      # the multiplier tries to compensate for high speed movement
      threshold = float(self.get('reroutingThreshold', REROUTING_DEFAULT_THRESHOLD))*self.reroutingThresholdMultiplier
      print("Divergence from route: %1.2f/%1.2f m computed in %1.0f ms" % (minDistance*1000, float(threshold), (1000 * (time.clock() - start1))) )
      return minDistance*1000 < threshold

  def _startTBTWorker(self):
    print "tbt: starting worker thread"
    startThread = True
    if not self.TBTWorker: # reuse previous thread or start new one
      self.TBTWorkerEnabled = True
      t = Thread(target=self._TBTWorker)
      t.daemon = True
      t.start()
      self.TBTWorker = t
    else:
      print "tbt: reusing worker thread"

  def _stopTBTWorker(self):
    self.TBTWorkerEnabled = False
    self.TBTWorker = None

  def _TBTWorker(self):
    """this function is run in its own thread and check if
    we are following the current route"""
    print("TBTWorker: started")
    while self.route and self.TBTWorkerEnabled:
      # first make sure automatic rerouting is enabled
      # eq. reroutingThreshold != None
      if self._automaticReroutingEnabled():
        # check if we are still following the route
#        print('TBTWorker: checking divergence from route')
        self.onRoute = self._followingRoute()
        if self._reroutingConditionsMet():
          print('TBTWorker: divergence detected')
          # switch to quick updates
          for i in range(0, REROUTING_TRIGGER_COUNT+1):
            time.sleep(1)
            onRoute = self._followingRoute()
            if onRoute: # divergence stopped
              self.onRoute = onRoute
              print('TBTWorker: false alarm')
              break
            else: # still diverging from current route
              self.onRoute = onRoute
              # increase divergence counter
              self.reroutingThresholdCrossedCounter+=1
              print('TBTWorker: increasing divergence counter (%d)' % self.reroutingThresholdCrossedCounter)
      time.sleep(REROUTE_CHECK_INTERVAL/1000.0)
    print("TBTWorker: shutting down")

  def getMonavTurns(self, monavResult):
    return instructions_generator.detectMonavTurns(monavResult)

  def shutdown(self):
    # cleanup
    self.stopTBT()
