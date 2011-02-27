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

  def say(self, text, language='en'):
    """say a given text"""

    # check if we are laready saying something
    with self.voiceLock:
      if self.speaking():
        # we are already speaking
        collisionString= "voice: message was not pronounced due to other message in progress"
        collisionString+= "\nlanguage code: \n%s\nmessage text:\n%s" % (language,text)
        print collisionString
      else:
        languageParam = '-v%s' % language
        self.espaekProcess = subprocess.Popen(['espeak', languageParam ,'-s 120','-m','"%s"' % text])

  def speaking(self):
    """return True if there is voice output in progress, False if not"""
    if self.espaekProcess: # is there a espeak process
      if self.espaekProcess.poll() != None: # none meens the process is still running
        return False # not talking
      else:
        return True # talking
    else:
      return False # no process, no talking

if(__name__ == "__main__"):
  a = example({}, {})
  a.update()
  a.update()
  a.update()
