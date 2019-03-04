from __future__ import with_statement # for python 2.5
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
from modules.base_module import RanaModule
import subprocess
import re
import threading


def getModule(*args, **kwargs):
    return Voice(*args, **kwargs)


class Voice(RanaModule):
    """Handle text to speech."""

    def __init__(self, *args, **kwargs):
        RanaModule.__init__(self, *args, **kwargs)
        self.espaekProcess = None
        # this lock is used to make sure there is only one voice speaking at once
        self.voiceLock = threading.Lock()
        # default espeak string for manual editing
        self.defaultStrings = {
            'espeak': 'espeak -v %language% -s 120 -a %volume% -m %qmessage%'
        }
        self.defaultProvider = "espeak"

    def firstTime(self):
        es = self.get("voiceString", None)
        if es is None:
            self.resetStringToDefault(self.defaultProvider)

    def resetStringToDefault(self, type):
        if type in self.defaultStrings:
            s = self.defaultStrings[type]
            self.log.info("resetting voice string to default using string for: %s", type)
            self.set("voiceString", s)
        else:
            self.log.info("can't reset string to default, no string for: %s", type)

    def getDefaultString(self, type):
        if type in self.defaultStrings:
            return self.defaultStrings[type]
        else:
            return ""

    def handleMessage(self, message, messageType, args):
        if messageType == "ms" and message == "resetStringToDefault" and "args":
            self.resetStringToDefault(args)
        elif message == "voiceTest":
            if self.get('soundEnabled', True):
                self.notify("Voice output test in progress", 3000)
                self.say("test. test. Can you hear me now ? Good.", "en")
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
                    distString = units.km2CurrentUnitString(distanceMeters / 1000.0, 1, False)
                    distString = '<p xml:lang="en">in <emphasis level="strong">' + distString + '</emphasis></p><br>'
                    # TODO: language specific distance strings
                output = distString + plaintextMessage

                if self.get('debugPrintVoiceMessages', False):
                    # the message can contain unicode, this might cause an exception when printing it
                    # in some systems (SHR-u on Neo, for example)
                    # outdated ^^^ (we are using logging now)
                    try:
                        self.log.info("saying: %s" % output)
                    except UnicodeEncodeError:
                        self.log.error("logging the current message to failed due to unicode conversion error")
                        # TODO: can this actually happen then using the Python logging module ?
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
                    if self.get('debugPrintVoiceMessages', False):
                        collisionString = "voice: message was not pronounced due to other message in progress"
                        collisionString += "\nlanguage code: \n%s\nmessage text:\n%s" % (language, text)
                        # the message can contain unicode, this might cause an exception when printing it
                        # in some systems (SHR-u on Neo, for example)
                        # outdated ^^^ (we are using logging now)
                        try:
                            self.log.debug("collision string: %s", collisionString)
                        except UnicodeEncodeError:
                            self.log.error("logging the current message failed due to unicode conversion error")
                            # TODO: can this actually happen then using the Python logging module
                    return False
                else:
                    self._speak(language, text)
                    return True

    def _speak(self, languageCode, message):
        """say a message wth espeak"""
        mode = self.get('voiceParameters', None)
        volume = "%d" % self._getEspeakVolumeValue()
        if mode == "manual": # user editable voice string
            voiceString = self.get("voiceString", None)
            if voiceString is not None:
                # replace language and message variables with appropriate values (if present)
                voiceString = re.sub("%language%", languageCode, voiceString) # language code
                voiceString = re.sub("%volume%", volume, voiceString) # volume
                voiceString = re.sub("%message%", message, voiceString) # message
                voiceString = re.sub("%qmessage%", '"%s"' % message, voiceString) # quoted message
                # the message can contain unicode, this might cause an exception when printing it
                #  in some systems (SHR-u on Neo FreeRunner, for example)"""
                try:
                    self.log.info("resulting custom voice string:\n%s", voiceString)
                except UnicodeEncodeError:
                    self.log.error("logging the current message failed due to unicode conversion error")
                self.espaekProcess = self._start_espeak_subprocess(voiceString, shell=True)

        # temporary hack to get some TTS output from espaek,
        # to be replaced by TTS handling code from Rinigius
        elif self.dmod.device_id == "jolla":
            languageParam = '-v%s' % languageCode
            args = "espeak --stdout %s -s 120 -a %s -m '%s' | gst-launch-1.0 -v fdsrc ! wavparse ! audioconvert ! autoaudiosink > /dev/null" % (languageParam, volume, message)
            self.espaekProcess = self._start_espeak_subprocess(args, shell=True)
        else:
            languageParam = '-v%s' % languageCode
            args = ['espeak', languageParam, '-s 120', '-a', '%s' % volume, '-m', '"%s"' % message]
            self.espaekProcess = self._start_espeak_subprocess(args)

    def _getEspeakVolumeValue(self):
        """get espeak volume value
        percentValue:
        100% - default
        200% - 2x default
        50% - 1/2 default
        The espeak value ranged from 0 to 200, with 100 being the default.
        Therefore -> 100% = 100 espeak value.
        """
        voiceVolumePercent = int(self.get('voiceVolume', 100))
        if voiceVolumePercent < 0:
            return 0 # minimum value for Espeak
        else:
            return voiceVolumePercent

    def _start_espeak_subprocess(self, args, shell=False):
        """start the voice output using the subprocess module and check for exceptions"""
        try:
            return subprocess.Popen(args, shell=shell)
        except TypeError:
            self.log.error("voice output failed - most probably due to the message containing unicode characters and your shell improperly supported unicode")
            return None
        except FileNotFoundError:
            self.log.error("espeak binary not found")
        except:
            self.log.exception("attempt to use espeak failed")


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
