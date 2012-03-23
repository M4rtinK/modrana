#!/usr/bin/python
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
from base_module import ranaModule
import geo
import math
import time
# only import GKT libs if GTK GUI is used
from core import gs
if gs.GUIString == "GTK":
  import pango
  import pangocairo

def getModule(m,d,i):
  return(turnByTurn(m,d,i))

class turnByTurn(ranaModule):
  """A turn by turn navigation module."""
  
  def __init__(self, m, d, i):
    ranaModule.__init__(self, m, d, i)
    gui = self.modrana.gui
    # initial colors
    self.navigationBoxBackground = (0,0,1,0.3) # very transparent blue
    self.navigationBoxText = (1,1,1,1) # non-transparent white

    self.goToInitialState()

  def goToInitialState(self):
    self.steps = []
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
    elif message == 'reroute':
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
    elif message == "toggleBoxHiding":
      print "turnByTurn: toggling navigation box visibility"
      self.navigationBoxHidden = not self.navigationBoxHidden
    elif message == "switchToPreviousTurn":
      self.switchToPreviousStep()
    elif message == "switchToNextTurn":
      self.switchToNextStep()
    elif message == "showMessageInsideNotification":
      currentStep = self.getCurrentStep()
      if currentStep:
        message = "<i>turn description:</i>\n%s" % currentStep['descriptionHtml']
        if self.dmod.hasNotificationSupport():
          self.dmod.notify(message,7000)
      #TODO: add support for modRana notifications once they support line wrapping

  def drawMapOverlay(self,cr):
      if self.steps:
        # get current step
        currentStep = self.getCurrentStep()
        proj = self.m.get('projection', None)
        # draw the current step indicator circle
        if currentStep and proj:
          lat = currentStep['Point']['coordinates'][1]
          lon = currentStep['Point']['coordinates'][0]
          (pointX, pointY) = proj.ll2xy(lat, lon)
          cr.set_source_rgb(1, 0, 0)
          cr.set_line_width(4)
          cr.arc(pointX, pointY, 12, 0, 2.0 * math.pi)
          cr.stroke()
          cr.fill()

  def drawScreenOverlay(self, cr):
    if self.steps: # is there something relevant to draw ?
    
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
#        background="generic:;;;;;"
        
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
          message = currentStep['descriptionHtml']
      
          # display current distance to the next point & other unit conversions
          units = self.m.get('units', None)
          if units and self.currentDistance:
            distString = units.m2CurrentUnitString(self.currentDistance,1,True)
            currentDistString = units.m2CurrentUnitString(currentStep['mDistanceFromStart'],1,True)
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
            # no need to draw a zero are layout
            return

          # get coordinates for the area available for text
          ulX,ulY = (bx+border,by+border+buttonStripOffset)
          cr.move_to(ulX,ulY)
          cr.save()
          if lh > usableHeight: # is the rendered text larger than the usable area ?
            clipHeight = 0
            # find last completley visible line
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
              #TODO: show the whole message in a notifications after clicking the scossors
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
          note = "%s/%s, %d/%d   <sub> tap this box to reroute</sub>" % (currentDistString, routeLengthString, self.currentStepIndex+1,len(self.steps))
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


  def sayTurn(self,message,distanceInMeters,forceLanguageCode=False):
    """say a text-to-spech message about a turn
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

      """ the message can contain unicode, this might cause an exception when printing it
      in some systems (SHR-u on Neo, for eaxmaple)"""
      try:
        print "saying: %s" % text
      except UnicodeEncodeError:
        print "voice: printing the current message to stdout failed do to unicode conversion error"

      if forceLanguageCode:
        espeakLanguageCode = forceLanguageCode
      else:
        # the espeak language code is the first part of this whitespace delimited string
        espeakLanguageCode = self.get('directionsLanguage', 'en en').split(" ")[0]
      return voice.say(text,espeakLanguageCode)

  def getStartingStep(self, which='first'):
    if self.steps:
      if which == 'first':
        return self.steps[0]
      if which == 'closest':
        return self.getClosestStep()

  def getClosestStep(self):
    proj = self.m.get('projection', None) # we also need the projection module
    pos = self.get('pos', None) # and current position
    if pos and proj:
      (lat1,lon1) = pos
      tempSteps = self.steps
      for step in tempSteps:
        lat2 = step['Point']['coordinates'][1]
        lon2 = step['Point']['coordinates'][0]
        step['currentDistance'] = geo.distance(lat1,lon1,lat2,lon2)*1000 # km to m
      closestStep = sorted(tempSteps, key=lambda x: x['currentDistance'])[0]
      return closestStep

  def getStep(self, id):
    """return steps for valid index, None otherwise"""
    maxIndex = len(self.steps) - 1
    if id > maxIndex or id < -(maxIndex+1):
      print "wrong turn index: %d, max index is: %d" % (id, maxIndex)
      return None
    else:
      return self.steps[id]

  def setStepAsCurrent(self, step):
    """set a given step as current step"""
    id = step['id']
    self.currentStepIndex = id

  def getCurrentStep(self):
    """return current step"""
    return self.steps[self.currentStepIndex]

  def getCurrentStepVisitStatus(self):
    """report visit status for  current step"""
    return self.steps[self.currentStepIndex]['visited']

  def markCurrentStepAsVisited(self):
    """mark current step as visited"""
    self.steps[self.currentStepIndex]['visited'] = True

  def switchToPreviousStep(self):
    """switch to previous step and clean up"""
    nextIndex = self.currentStepIndex - 1
    if nextIndex >= 0:
      self.currentStepIndex = nextIndex
      self.espeakFirstTrigger = False
      self.espeakSecondTrigger = False
      print "switching to previous step"
    else:
      print "previous step reached"

  def switchToNextStep(self):
    """switch to next step and clean up"""
    maxIndex = len(self.steps) - 1
    nextIndex = self.currentStepIndex + 1
    if nextIndex <= maxIndex:
      self.currentStepIndex = nextIndex
      self.espeakFirstAndHalfTrigger = False
      self.espeakFirstTrigger = False
      self.espeakSecondTrigger = False
      print "switching to next step"
    else:
      print "last step reached"

  def enabled(self):
    """return True if enabled, false othervise"""
    if self.steps:
      return True
    else:
      return False

  def startTBT(self, fromWhere='first'):
    """start Turn-by-turn navigation"""

    # clean up any possible previous navigation data
    self.goToInitialState()

    """NOTE: turn and step are used interchangably in the documentation"""
    m = self.m.get('route', None)
    if m:
      (dirs,routeRequestSentTimestamp) = m.getCurrentDirections()
      if dirs: # is the route nonempty ?
        # show the warning message
        self.sendMessage('ml:notification:m:use at own risk, watch for cliffs, etc.;3')
        route = dirs['Directions']['Routes'][0]
        # for some reason the combined distance does not account for the last step
        self.mRouteLength = route['Distance']['meters'] + route['Steps'][-1]["Distance"]["meters"]
        self.steps = []
        mDistanceFromStart = route['Steps'][-1]["Distance"]["meters"]
        for step in route['Steps']:
          step['currentDistance'] = None # add the currentDistance key
          # add and compute the distance from start
          step['mDistanceFromStart'] = mDistanceFromStart
          mDistanceFromLast = step["Distance"]["meters"]
          mDistanceFromStart = mDistanceFromStart + mDistanceFromLast
          self.steps.append(step)
        self.steps = dirs['Directions']['Routes'][0]['Steps']
        # some statistics
        metersPerSecSpeed = self.get('metersPerSecSpeed', None)
        dt = time.time() - routeRequestSentTimestamp
        print "route lookup took: %f s" % dt
        if dt and metersPerSecSpeed:
          dm = dt * metersPerSecSpeed
          print "distance traveled during lookup: %f m" % dm
        """the duration of the road lookup and other variables are currently not used
        in the heuristics but might be added later to make the heursitics more robust"""


        """now we decide if we use the closest turn, or the next one,
        as we might be already past it and on our way to the next turn"""
        cs = self.getClosestStep() # get geographically closest step
        pos = self.get('pos', None) # get current position
        pReachedDist = int(self.get('pointReachedDistance', 30)) # get the trigger distance
        nextTurnId = cs['id'] + 1
        nextStep = self.getStep(nextTurnId)
        # check if we have all the data needed for our heuristics
        print "tbt: trying to guess correct step to start navigation"
        if nextStep and pos and pReachedDist:
          (lat,lon) = pos
          (csLat,csLon) = (cs['Point']['coordinates'][1],cs['Point']['coordinates'][0])
          (nsLat,nsLon) = (nextStep['Point']['coordinates'][1],nextStep['Point']['coordinates'][0])
          pos2nextStep = geo.distance(lat,lon,nsLat,nsLon)*1000
          pos2currentStep = geo.distance(lat,lon,csLat,csLon)*1000
          currentStep2nextStep = geo.distance(csLat,csLon,nsLat,nsLon)*1000
#          print "pos",(lat,lon)
#          print "cs",(csLat,csLon)
#          print "ns",(nsLat,nsLon)
          print "position to next turn: %f m" % pos2nextStep
          print "position to current turn: %f m" % pos2currentStep
          print "current turn to next turn: %f m" % currentStep2nextStep
          print "turn reached trigger distance: %f m" % pReachedDist

          if pos2currentStep > pReachedDist:
            """this means we are out of the "capture circle" of the closest step"""

            """what is more distant, the closest or the next step ?"""
            if pos2nextStep < currentStep2nextStep:
              """we are mosty probably already past the closest step,
              so we switch to the next step at once"""
              print "tbt: already past closest turn, switching to next turn"
              self.setStepAsCurrent(nextStep)
              """we play the message for the next step,
              with current distance to this step,
              to assure there is some voice output immediatelly after
              getting a new route or rerouting"""
              plaintextMessage = nextStep['descriptionEspeak']
              self.sayTurn(plaintextMessage, pos2nextStep)


            else:
              """we have probably not yet reached the closest step,
                 so we start navigation from it"""
              print "tbt: closest turn not yet reached"
              self.setStepAsCurrent(cs)

          else:
            """we are inside the  "capture circle" of the closest step,
            this meens the navigation will trigger the voice message by itself
            and correctly switch to next step
            -> no need to switch to next step from here"""
            print "tbt: inside reach distance of closest turn"
            self.setStepAsCurrent(cs)

        else:
          """we dont have some of the data, that is needed to decide
          if we start the navigation from the closest step of from the step that is after it
          -> we just start from the closest step"""
          """tbt: not enough data to decide, using closest turn"""
          self.setStepAsCurrent(cs)
    self.doNavigationUpdate() # run a first time navigation update
    self.locationWatchID = self.watch('locationUpdated', self.locationUpdateCB)
    print("tbt: started")
      
  def stopTBT(self):
    """stop Turn-by-turn navigation"""
    # remove location watch
    if self.locationWatchID:
      self.removeWatch(self.locationWatchID)
    
    self.goToInitialState()
    print("tbt: stopped")

  def locationUpdateCB(self, key, newValue, oldValue):
    """position chnaged, do a tbt navigation update"""
    if key == "locationUpdated": # just to be sure
      self.doNavigationUpdate()
    else:
      print "tbt: invalid key: %r" % key

  def doNavigationUpdate(self):
    """do a navigation update"""
    # make sure there really are some steps
    if not self.steps:
      print "tbt: error no navigation steps"
      return
    pos = self.get('pos', None)
    if pos == None:
      print "tbt: skipping update, invalid position"
      return

    # get/compute/update necessary the values
    (lat1,lon1) = pos
    currentStep = self.getCurrentStep()
    lat2 = currentStep['Point']['coordinates'][1]
    lon2 = currentStep['Point']['coordinates'][0]
    currentDistance = geo.distance(lat1,lon1,lat2,lon2)*1000 # km to m
    self.currentDistance = currentDistance # update current distance

    # use some sane minimum distance
    distance = int(self.get('minAnnounceDistance',100))

    # GHK: make distance speed-sensitive
    #
    # I came up with this formula after a lot of exerimentation with
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
      if metersPerSecSpeed > pointReachedDistance*0.75:
        pointReachedDistance = metersPerSecSpeed*2
        print "tbt: enlarging point reached distance to: %1.2f m due to large speed (%1.2f m/s)" % (pointReachedDistance, metersPerSecSpeed)

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
        print "#####"
        print "min/max announce time: %d/%d s" % (lowTime, highTime)
        print "trigger distance: %1.2f m (%1.2f s warning)" % (distance, distance/float(metersPerSecSpeed))
        print "current distance: %1.2f m" % currentDistance
        print "current speed: %1.2f m/s (%1.2f km/h)" % (metersPerSecSpeed, metersPerSecSpeed*3.6)
        print "point reached distance: %f m" % pointReachedDistance
        print "1. triggered=%r, 1.5. triggered=%r, 2. triggered=%r" % (self.espeakFirstTrigger, self.espeakFirstAndHalfTrigger, self.espeakSecondTrigger)
        if warnTime > 30:
          print "optional (20 s) trigger distance: %1.2f" % (20.0*metersPerSecSpeed)

      if currentDistance <= pointReachedDistance:
        """this means we reached the point"""
        if self.espeakSecondTrigger == False:
          print "triggering espeak nr. 2"
          # say the message without distance
          plaintextMessage = currentStep['descriptionEspeak']
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
            print "triggering espeak nr. 1"
            plaintextMessage = currentStep['descriptionEspeak']
            if self.sayTurn(plaintextMessage, currentDistance):
              self.espeakFirstTrigger = True # first message done
        if self.espeakFirstAndHalfTrigger == False and warnTime > 30:
          if currentDistance <= (20.0*metersPerSecSpeed):
            """in case that the warning time gets too big, add an intemediate warning at 20 secconds
            NOTE: this means it is said after the first trigger
            """
            plaintextMessage = currentStep['descriptionEspeak']
            if self.sayTurn(plaintextMessage, currentDistance):
              self.espeakFirstAndHalfTrigger = True # intermediate message done

              
if(__name__ == "__main__"):
  a = example({}, {})
  a.update()
  a.update()
  a.update()
