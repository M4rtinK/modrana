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
import subprocess
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
    self.espaekProcess = None

    
  def handleMessage(self, message, type, args):
    if message == 'start':
      self.startTBT()
      if type == 'ms':
        if args == 'first':
          self.currentStepIndex = 0
        elif args == 'closest':
          cs = self.getClosestStep()
          id = cs['id']
          self.currentStepIndex = id
    elif message == 'stop':
      self.stopTBT()
    elif message == 'reroute':
      # 1. say rerouting is in progress
      message = "rerouting"
      self.espeakSay(message, 0, "en") # make sure rerouting said with english voice
      time.sleep(2) #TODO: improve this
      # 2. get a new route from current position to destination
      self.sendMessage("ms:route:reroute:fromPosToDest")
      # 3. restart routing for to this new route from the closest point
      self.sendMessage("ms:turnByTurn:start:closest")

  def drawMapOverlay(self,cr):
      if self.currentStepIndicator:
        (pointX, pointY) = self.currentStepIndicator
        cr.set_source_rgb(1, 0, 0)
        cr.set_line_width(4)
        cr.arc(pointX, pointY, 12, 0, 2.0 * math.pi)
        cr.stroke()
        cr.fill()

  def drawScreenOverlay(self, cr):
    if self.steps: # is there something relevant to draw ?
      proj = self.m.get('projection', None) # we also need the projection module
      
      currentStep = self.getCurrentStep()
      distance = currentStep['Distance']['meters']
      pos = self.get('pos', None) # and current position
      (lat1,lon1) = pos
      lat2 = currentStep['Point']['coordinates'][1]
      lon2 = currentStep['Point']['coordinates'][0]
      currentDistance = geo.distance(lat1,lon1,lat2,lon2)*1000 # km to m
      pointReachedDistance = int(self.get('pointReachedDistance', 30))

      # TODO: maybe move the espeak messages from the display code ?
      if distance>=currentDistance:
        """this means we reached an optimal distance for saying the message"""
        if self.espeakFirstTrigger == False:
          print "triggering espeak nr. 1"
          outputFree = True
          if self.espaekProcess:
            if self.espaekProcess.poll() == None:
              outputFree = False # espeak is talking at the moment
          if outputFree:
            plaintextMessage = currentStep['descriptionEspeak']
            self.espeakSay(plaintextMessage, currentDistance)
            self.espeakFirstTrigger = True # everything has been said :D
      if currentDistance <= pointReachedDistance:
        """this means we reached the point"""
        self.switchToNextStep() # switch to next step
        if self.espeakSecondTrigger == False:
          print "triggering espeak nr. 2"
          outputFree = True
          if self.espaekProcess:
            if self.espaekProcess.poll() == None:
              outputFree = False # espeak is talking at the moment
          if outputFree:
            # say the message without distance
            plaintextMessage = currentStep['descriptionEspeak']
            self.espeakSay(plaintextMessage, 0)
            self.markCurrentStepAsVisited() # mark this point as visited
            self.espeakSecondTrigger = True # everything has been said, again :D

      # draw the current step indicator circle
      lat = currentStep['Point']['coordinates'][1]
      lon = currentStep['Point']['coordinates'][0]

      self.currentStepIndicator = proj.ll2xy(lat, lon)
#      cr.set_source_rgb(1, 0, 0)
#      cr.set_line_width(4)
#      cr.arc(pointX, pointY, 12, 0, 2.0 * math.pi)
#      cr.stroke()
#      cr.fill()

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
        # create a layout for your drawing area
        layout = pg.create_layout()
        message = currentStep['descriptionHtml']

        # display current distance to the next point
        units = self.m.get('units', None)
        if units:
          distString = units.m2CurrentUnitString(currentDistance,2)

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


  def espeakSay(self, plaintextMessage, distanceMeters, forceLanguageCode=False):
    """say routing messages through espeak"""
    units = self.m.get('units', None)
    if units:
      if distanceMeters == 0:
        distString = ""
      else:
        distString = units.km2CurrentUnitString(distanceMeters/1000.0, 1, False)
        distString = '<p xml:lang="en">in <emphasis level="strong">'+ distString + '</emphasis></p><br>'
        # TODO: language specific distance strings
      output = distString + plaintextMessage
      print "saying: %s" % output
      if forceLanguageCode:
        espeakLanguageCode = forceLanguageCode
      else:
        # the espeak language code is the fisrt part of this whitespace delimited string
        espeakLanguageCode = self.get('directionsLanguage', 'en en').split(" ")[0]
      languageParam = '-v%s' % espeakLanguageCode
      self.espaekProcess = subprocess.Popen(['espeak', languageParam ,'-s 120','-m','"%s"' % output])

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
    """return True if enabled, flase othervise"""
    if self.steps:
      return True
    else:
      return False

  def startTBT(self):
    # start Turn-by-turn navigation
    m = self.m.get('route', None)
    if m:
      dirs = m.getCurrentDirections()
      if dirs: # is the route nonempty ?
        print dirs
        self.sendMessage('notification:use at own risk, watch for cliffs, etc.#2')
        route = dirs['Directions']['Routes'][0]
        self.steps = []
        for step in route['Steps']:
          step['currentDistance'] = None # add the currentDistance key
          self.steps.append(step)
        self.steps = dirs['Directions']['Routes'][0]['Steps']

  def stopTBT(self):
    # stop Turn-by-turn navigation
    self.goToInitialState()



if(__name__ == "__main__"):
  a = example({}, {})
  a.update()
  a.update()
  a.update()
