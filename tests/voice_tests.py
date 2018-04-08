# -*- coding: utf-8 -*-

# Copyright (C) 2017 Osmo Salomaa
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

import os
import tempfile
import time
import unittest

from core import voice
from core import threads
threads.initThreading()

class TestVoiceGenerator(unittest.TestCase):

    def setUp(self):
        self.generator = voice.VoiceGenerator()

    def _test_an_engine(self, engine):
        """Test individual voice engines."""
        if not engine.supports("en"):
            return
        handle, fname = tempfile.mkstemp(dir=self.generator._tmpdir)
        engine("en").make_wav("just testing", fname)
        self.assertTrue(os.path.isfile(fname))
        self.assertTrue(os.path.getsize(fname) > 256)

    @unittest.skipUnless(voice.VoiceEngineMimic.available(), "Mimic not installed")
    def mimic_test(self):
        """Test using the Mimic TTS engine"""
        self._test_an_engine(engine=voice.VoiceEngineMimic)

    @unittest.skipUnless(voice.VoiceEngineFlite.available(), "Flite not installed")
    def flite_test(self):
        """Test using the Flite TTS engine"""
        self._test_an_engine(engine=voice.VoiceEngineFlite)

    @unittest.skipUnless(voice.VoiceEnginePicoTTS.available(), "PicoTTS not installed")
    def picotts_test(self):
        """Test using the PicoTTS engine"""
        self._test_an_engine(engine=voice.VoiceEnginePicoTTS)

    @unittest.skipUnless(voice.VoiceEngineEspeak.available(), "Espeak not installed")
    def espeak_test(self):
        """Test using the Espeak TTS engine"""
        self._test_an_engine(engine=voice.VoiceEngineEspeak)

    def clean_test(self):
        """Test voice generator cleanup"""
        self.generator.set_voice("en")
        self.generator.make("just testing")
        # this is a little dirty but rather join the
        # task queue rather than to introduce an arbitrary
        # waiting for the worker thread to finish
        self.generator._task_queue.join()
        self.generator.clean()
        self.assertFalse(os.listdir(self.generator._tmpdir))

    def get_test(self):
        """Test getting a voice sample"""
        self.generator.set_voice("en")
        if not self.generator.active: return
        self.generator.make("just testing")
        # this is a little dirty but rather join the
        # task queue rather than to introduce an arbitrary
        # waiting for the worker thread to finish
        self.generator._task_queue.join()
        fname = self.generator.get("just testing")
        self.assertTrue(os.path.isfile(fname))
        self.assertTrue(os.path.getsize(fname) > 256)

    def make_test(self):
        """Test voice sample creation"""
        self.generator.set_voice("en")
        self.generator.make("just testing")
        # this is a little dirty but rather join the
        # task queue rather than to introduce an arbitrary
        # waiting for the worker thread to finish
        self.generator._task_queue.join()

    def quit_test(self):
        """Check voice generator shutdown"""
        self.generator.set_voice("en")
        self.generator.make("just testing")
        # this is a little dirty but rather join the
        # task queue rather than to introduce an arbitrary
        # waiting for the worker thread to finish
        self.generator._task_queue.join()
        self.generator.quit()
        self.assertFalse(os.path.isdir(self.generator._tmpdir))

    def set_voice_test(self):
        """Check setting voice"""
        self.generator.set_voice("en")
        self.generator.set_voice("en", "male")
        self.generator.set_voice("en", "female")
        self.generator.set_voice("en_US")
        self.generator.set_voice("en_XX")
