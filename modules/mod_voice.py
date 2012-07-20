from __future__ import with_statement # for python 2.5
#!/usr/bin/python
# -*- coding: utf-8 -*-
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
import re
import threading

def getModule(m,d,i):
  return(voice(m,d,i))

class voice(ranaModule):
  """Handle text to speech."""
  
  def __init__(self, m, d, i):
    ranaModule.__init__(self, m, d, i)
    self.espaekProcess = None
    # this lock is used to make sure there is only one voice speaking at once
    self.voiceLock = threading.Lock()
    # default espeak string for manual editing
    self.defaultStrings = {
                          'espeak' : 'espeak -v %language% -s 120 -m %qmessage%'
                          }
    self.defaultProvider = "espeak"



  def firstTime(self):
    es = self.get("voiceString", None)
    if es is None:
      self.resetStringToDefault(self.defaultProvider)

  def resetStringToDefault(self, type):
    if type in self.defaultStrings:
      s = self.defaultStrings[type]
      print "voice: resetting voice string to default using string for: %s" % type
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
    elif message == "voiceTest":
      if self.get('soundEnabled', True):
        self.notify("Voice output test in progress", 3000)
        self.say("test. test. Can you hear me now ? Good.","en")
      else:
        self.notify("Sound output disabled, can't test", 2000)

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


          """ the message can contain unicode, this might cause an exception when printing it
          in some systems (SHR-u on Neo, for example)"""
          try:
            print "saying: %s" % output
          except UnicodeEncodeError:
            print "voice: printing the current message to stdout failed do to unicode conversion error"
          if forceLanguageCode:
            espeakLanguageCode = forceLanguageCode
          else:
            # the espeak language code is the first part of this whitespace delimited string
            espeakLanguageCode = self.get('directionsLanguage', 'en en').split(" ")[0]
          self._speak(espeakLanguageCode, output)

  def say(self, text, language='en'):
    """say a given text.  Return false if failed due to collision"""
    if self._isEnabled():
      # check if we are already saying something
      with self.voiceLock:
        if self.speaking():
          # we are already speaking
          collisionString= "voice: message was not pronounced due to other message in progress"
          collisionString+= "\nlanguage code: \n%s\nmessage text:\n%s" % (language,text)
          """ the message can contain unicode, this might cause an exception when printing it
          in some systems (SHR-u on Neo, for example)"""
          try:
            print collisionString
          except UnicodeEncodeError:
            print "voice: printing the current message to stdout failed do to unicode conversion error"
          return False


        else:
          self._speak(language, text)
          return True

  def _speak(self, languageCode, message):


    mode = self.get('voiceParameters', None)
    if mode == "manual": # user editable voice string
      voiceString = self.get("voiceString", None)
      if voiceString is not None:

        # replace language and message variables with appropriate values (if present)
        voiceString = re.sub("%language%", languageCode, voiceString)

        voiceString = re.sub("%message%", message, voiceString)

        voiceString = re.sub("%qmessage%", '"%s"' % message, voiceString)
        
        """ the message can contain unicode, this might cause an exception when printing it
        in some systems (SHR-u on Neo, for example)"""
        try:
          print "voice: resulting custom voice string:\n%s" % voiceString
        except UnicodeEncodeError:
          print "voice: printing the current message to stdout failed do to unicode conversion error"

        self.espaekProcess = self._startSubprocess(voiceString, shell=True)
    else:
      languageParam = '-v%s' % languageCode
      args = ['espeak', languageParam ,'-s 120','-m','"%s"' % message]
      self.espaekProcess = self._startSubprocess(args)

  def _startSubprocess(self, args, shell=False):
    """start the voice output using the subprocess module and check for exceptions"""
    try:
      return subprocess.Popen(args, shell=shell)
    except TypeError:
      print "voice: voice output failed - most probably due to the message containing unicode characters and your shell not properly supporting unicode"
      return None


  def speaking(self):
    """return True if there is voice output in progress, False if not"""
    if self.espaekProcess: # is there a espeak process
      if self.espaekProcess.poll() is not None: # none means the process is still running
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
