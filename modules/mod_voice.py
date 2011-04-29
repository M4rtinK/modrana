from __future__ import with_statement # for python 2.5
#!/usr/bin/python
#----------------------------------------------------------------------------
# A module for handling handling text to speach.
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
import subprocess
import shlex
import re
import threading

def getModule(m,d,i):
  return(voice(m,d,i))

class voice(ranaModule):
  """Handle text to speach."""
  
  def __init__(self, m, d, i):
    ranaModule.__init__(self, m, d, i)
    self.espaekProcess = None
    # this lock is used to make sure there is only one voice speking at once
    self.voiceLock = threading.Lock()
    # default espeak string for manual editing
    self.defaultStrings = {
                          'espeak' : 'espeak -v %language -s 120 -m %message'
                          }
    self.defaultProvider = "espeak"



  def firstTime(self):
    es = self.get("voiceString", None)
    if es == None:
      self.resetStringToDefault(self.defaultProvider)

  def resetStringToDefault(self, type):
    if type in self.defaultStrings:
      s = self.defaultStrings[type]
      print "voice: reseting voice string to default using string for: %s" % type
      self.set("voiceString", s)
    else:
      print "voice: cant reset string to default, no string for:", type

  def getDefaultString(self, type):
    if type in self.defaultStrings:
      return self.defaultStrings[type]
    else:
      return ""

  def handleMessage(self, message, type, args):
    if type == "ms" and message == "resetStringToDefault" and "args":
      self.resetStringToDefault(args)
    
  def espeakSay(self, plaintextMessage, distanceMeters, forceLanguageCode=False):
      """say routing messages through espeak"""
      if self._isEnabled():
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
          self._speak(espeakLanguageCode, output)

  def say(self, text, language='en'):
    """say a given text"""
    if self._isEnabled():
      # check if we are laready saying something
      with self.voiceLock:
        if self.speaking():
          # we are already speaking
          collisionString= "voice: message was not pronounced due to other message in progress"
          collisionString+= "\nlanguage code: \n%s\nmessage text:\n%s" % (language,text)
          print collisionString
        else:
          self._speak(language, text)

  def _speak(self, languageCode, message):


    mode = self.get('voiceParameters', None)
    if mode == "manual": # user editable voice string
      voiceString = self.get("voiceString", None)
      if voiceString != None:

        # replace langauge and message variables with appropriate values (if present)
        voiceString = re.sub("%language", languageCode, voiceString)

        message = '"%s"' % message # add quotes
        voiceString = re.sub("%message", message, voiceString)
        print "voice: resulting custom voice string:\n%s" % voiceString
        self.espaekProcess = subprocess.Popen(voiceString, shell=True)
    else:
      languageParam = '-v%s' % languageCode
      args = ['espeak', languageParam ,'-s 120','-m','"%s"' % message]
      self.espaekProcess = subprocess.Popen(args)


  def speaking(self):
    """return True if there is voice output in progress, False if not"""
    if self.espaekProcess: # is there a espeak process
      if self.espaekProcess.poll() != None: # none meens the process is still running
        return False # not talking
      else:
        return True # talking
    else:
      return False # no process, no talking

  def _isEnabled(self):
    if self.get('soundEnabled', True):
      return True
    else:
      return False

if(__name__ == "__main__"):
  a = example({}, {})
  a.update()
  a.update()
  a.update()
