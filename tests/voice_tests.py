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

class TestVoiceGenerator(unittest.TestCase):

    def setUp(self):
        self.generator = voice.VoiceGenerator()

    @unittest.skip("enable this after engine lookup is fixed")
    def engines_test(self):
        """Test individual voice engines"""
        for engine in self.generator.engines:
            if not engine.supports("en"): continue
            handle, fname = tempfile.mkstemp(dir=self.generator._tmpdir)
            engine("en").make_wav("just testing", fname)
            self.assertTrue(os.path.isfile(fname))
            self.assertTrue(os.path.getsize(fname) > 256)

    def clean_test(self):
        """Test voice generator cleanup"""
        self.generator.set_voice("en")
        self.generator.make("just testing")
        time.sleep(1)
        self.generator.clean()
        self.assertFalse(os.listdir(self.generator._tmpdir))

    def get_test(self):
        """Test getting a voice sample"""
        self.generator.set_voice("en")
        if not self.generator.active: return
        self.generator.make("just testing")
        time.sleep(1)
        fname = self.generator.get("just testing")
        self.assertTrue(os.path.isfile(fname))
        self.assertTrue(os.path.getsize(fname) > 256)

    def make_test(self):
        """Test voice sample creation"""
        self.generator.set_voice("en")
        self.generator.make("just testing")
        time.sleep(1)

    def quit_test(self):
        """Check voice generator shutdown"""
        self.generator.set_voice("en")
        self.generator.make("just testing")
        time.sleep(1)
        self.generator.quit()
        self.assertFalse(os.path.isdir(self.generator._tmpdir))

    def set_voice_test(self):
        """Check setting voice"""
        self.generator.set_voice("en")
        self.generator.set_voice("en", "male")
        self.generator.set_voice("en", "female")
        self.generator.set_voice("en_US")
        self.generator.set_voice("en_XX")
