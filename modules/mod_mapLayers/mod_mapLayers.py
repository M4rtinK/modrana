# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Sample of a modRana module.
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

def getModule(m,d,i):
  return MapLayers(m,d,i)

class MapLayers(RanaModule):
  """A sample modRana module"""
  
  def __init__(self, m, d, i):
    RanaModule.__init__(self, m, d, i)

class MapLayer(object):
  """A map layer"""

  def __init__(self, layerId, config):
    """
    :param config: a dictionary with map layer configuration
    :type config: dict
    """
    self.config = config
    self._layerId = layerId

  @property
  def id(self):
    """
    :return: unique map layer identifier
    """
    return self._layerId

  @property
  def label(self):
    return self.config['label']

  @property
  def url(self):
    return self.config['url']

  @property
  def type(self):
    return self.config['type']

  @property
  def maxZoom(self):
    return self.config['max_zoom']

  @property
  def minZoom(self):
    return self.config['min_zoom']

  @property
  def folderPrefix(self):
    return self.config['folder_prefix']

  @property
  def coordinates(self):
    return self.config['coordinates']

  @property
  def groupId(self):
    return self.config.get('group', None)

class MapLayerGroup(object):
  """A group of map layers"""
  def __init__(self, groupId, config, layerIds=None):
    """
    :param groupId: unique map layer group identifier
    :param config: a dictionary with map layer configuration
    :param layerIds: a list of map layer identifiers that are part of the group
    """
    if not layerIds: layerIds = []
    self._layerIds = layerIds
    self._groupId = groupId
    self._config = config

  @property
  def id(self):
    """
    :return: unique map layer group identifier
    """
    return self._groupId

  @property
  def label(self):
    return self._config['label']

  @property
  def mapLayerIds(self):
    return self._layerIds