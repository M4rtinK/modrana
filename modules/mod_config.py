# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Configuration options
#
# Rename this file to mod_config.py to use it
#----------------------------------------------------------------------------
# Copyright 2007-2008, Oliver White
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

def getModule(m,d,i):
  return Config(m,d,i)

class Config(RanaModule):
  """Handle configuration, options, and setup"""
  def __init__(self, m, d, i):
    RanaModule.__init__(self, m, d, i)

  def firstTime(self):

    # *** Various hardcoded persistent variables ***

    # Option: Number of threads for batch-downloading tiles
    self.set('maxBatchThreads', 5)

    # Option: Bath tile download threads
    # this sets the number of threads for bach tile download
    # even values of 10 can lead to 3000+ open sockets on a fast internet connection
    # handle with care :)
    # UPDATE: modRana now reuses open sockets so it might not be that bad any more
    self.set('maxDlThreads', 5)
    # Option: Batch size estimation threads
    # this sets the number of threads used for determining the size of the batch (from http headers)
    # NOTE: even though we are downloading only the headers,
    # for a few thousand tiles this can be an un-trivial amount of data
    # (so use this with caution on metered connections)
    self.set('maxSizeThreads', 20)

    # Google API key for modRana
    self.set('googleAPIKey', 'ABQIAAAAv84YYgTIjdezewgb8xl5_xTKlax5G-CAZlpGqFgXfh-jq3S0yRS6XLrXE9CkHPS6KDCig4gHvHK3lw')

    # Option: set your start position
    #self.set("pos", (49.2, 16.616667)) # Brno