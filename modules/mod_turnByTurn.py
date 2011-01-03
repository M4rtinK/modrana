#!/usr/bin/python
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
import pango
import pangocairo
import time

def getModule(m,d):
  return(turnByTurn(m,d))

class turnByTurn(ranaModule):
  """A turn by turn navigation module."""
  
  def __init__(self, m, d):
    ranaModule.__init__(self, m, d)
    self.goToInitialState()

  def goToInitialState(self):
    self.steps = []
    self.currentStepIndex = None
    self.currentStepIndicator = None
    self.espeakFirstTrigger = False
    self.espeakSecondTrigger = False
    self.navigationUpdateInterval = 1 # update navigation info once per second
    self.lastNavigationUpdate=time.time()
    self.currentDistance = None
    self.currentStep = None

    
  def update(self):
    # check if we should trigger a navigation message
    
    # is navigation on ?
    if self.steps:
      # respect the navigation update interval
      timestamp = time.time()
      if timestamp - self.lastNavigationUpdate >= self.navigationUpdateInterval:
        self.lastNavigationUpdate = timestamp
        self.doNavigationUpdate()

  def doNavigationUpdate(self):
    """do a navigation update"""
    # get/compute/update necessary the values
    pos = self.get('pos', None) # and current position
    (lat1,lon1) = pos
    currentStep = self.getCurrentStep()
    lat2 = currentStep['Point']['coordinates'][1]
    lon2 = currentStep['Point']['coordinates'][0]
    currentDistance = geo.distance(lat1,lon1,lat2,lon2)*1000 # km to m
    self.currentDistance = currentDistance # update current distance
    distance = currentStep['Distance']['meters']
    pointReachedDistance = int(self.get('pointReachedDistance', 30))

    if distance>=currentDistance:
      """this means we reached an optimal distance for saying the message"""
      if self.espeakFirstTrigger == False:
        print "triggering espeak nr. 1"
        plaintextMessage = currentStep['descriptionEspeak']
        self.sayTurn(plaintextMessage, currentDistance)
        self.espeakFirstTrigger = True # everything has been said :D
    if currentDistance <= pointReachedDistance:
      """this means we reached the point"""
      self.switchToNextStep() # switch to next step
      if self.espeakSecondTrigger == False:
        print "triggering espeak nr. 2"
        # say the message without distance
        plaintextMessage = currentStep['descriptionEspeak']
        self.sayTurn(plaintextMessage, 0)
        self.markCurrentStepAsVisited() # mark this point as visited
        self.espeakSecondTrigger = True # everything has been said, again :D


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
      if vport:
        # background
        cr.set_source_rgba(0, 0, 1, 0.3)
        (sx,sy,w,h) = vport
        (bx,by,bw,bh) = (w*0.15,h*0.1,w*0.7,h*0.4)
        cr.rectangle(bx,by,bw,bh)
        cr.fill()
        cr.set_source_rgba(1, 1, 1, 1)
        pg = pangocairo.CairoContext(cr)
        # create a layout for our drawing area
        layout = pg.create_layout()
        message = currentStep['descriptionHtml']

        # display current distance to the next point
        units = self.m.get('units', None)
        if units and self.currentDistance:
          distString = units.m2CurrentUnitString(self.currentDistance,2)
        else:
          distString = ""

        note = "<sub> tap this box to reroute</sub>"
        message = distString + "\n" + message + "\n\n" + note

        border = min(w/30.0,h/30.0)
        layout.set_markup(message)
        layout.set_font_description(pango.FontDescription("Sans Serif 20"))
        # scale to text to fit into the box
        (lw,lh) = layout.get_size()
        if lw == 0 or lh == 0:
          return
        scale = float(pango.SCALE)
        factor = min(((bw-2*border)/(lw/scale)),((bh-2*border)/(lh/scale)))
        factor = min(factor, 1.0)
        cr.move_to(bx+border,by+border)
        cr.save()
        cr.scale(factor,factor)
        pg.show_layout(layout)
        cr.restore()
        # make clickable
        clickHandler = self.m.get('clickHandler', None)
        if clickHandler:
          action = "turnByTurn:reroute"
          clickHandler.registerXYWH(bx, by , bw, bh, action)

  def sayTurn(self,message,distanceInMeters,forceLanguageCode=False):
    """say a text-to-spech message about a turn
       this basically wraps the simple say method from voice and adds some more information,
       like current distance to the turn
       """
    voice = self.m.get('voice', None)
    units = self.m.get('units', None)
    if voice and units:
      if distanceInMeters == 0:
        distString = ""
      else:
        distString = units.km2CurrentUnitString(distanceInMeters/1000.0, 1, False)
        distString = '<p xml:lang="en">in <emphasis level="strong">'+ distString + '</emphasis></p><br>'
        # TODO: language specific distance strings
      text = distString + message
      print "saying: %s" % text
      if forceLanguageCode:
        espeakLanguageCode = forceLanguageCode
      else:
        # the espeak language code is the first part of this whitespace delimited string
        espeakLanguageCode = self.get('directionsLanguage', 'en en').split(" ")[0]
      voice.say(text,espeakLanguageCode)

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

  def switchToNextStep(self):
    """switch to next step and clean up"""
    maxIndex = len(self.steps) - 1
    nextIndex = self.currentStepIndex + 1
    if nextIndex <= maxIndex:
      self.currentStepIndex = nextIndex
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
        self.sendMessage('notification:use at own risk, watch for cliffs, etc.#2')
        route = dirs['Directions']['Routes'][0]
        self.steps = []
        for step in route['Steps']:
          step['currentDistance'] = None # add the currentDistance key
          self.steps.append(step)
        self.steps = dirs['Directions']['Routes'][0]['Steps']
#        if fromWhere == 'first':
#          self.currentStepIndex = 0
#        elif fromWhere == 'closest':
#          cs = self.getClosestStep()
#          id = cs['id']
#          self.currentStepIndex = id
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
    self.doNavigationUpdate() # run a navigation update

  def stopTBT(self):
    """stop Turn-by-turn navigation"""
    self.goToInitialState()

if(__name__ == "__main__"):
  a = example({}, {})
  a.update()
  a.update()
  a.update()
