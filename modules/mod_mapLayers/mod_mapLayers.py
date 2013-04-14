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
from core.signal import Signal

# lists keys that need to be defined for a layer
# in the map configuration file to be valid,
# otherwise the layer will be rejected
# defined for use in modRana


# due to Python 2.5 compatibility
# we use the set([item,item,item]) syntax
# instead of {item,item,item}
MAP_LAYER_REQUIRED_KEYS = set([
  'label',
  'url',
  'max_zoom',
  'min_zoom',
  'type',
  'folder_prefix',
  'coordinates'
])

MAP_LAYER_GROUP_REQUIRED_KEYS = set([
  'label'
])


def getModule(m,d,i):
  return MapLayers(m,d,i)

class MapLayers(RanaModule):
  """A sample modRana module"""
  
  def __init__(self, m, d, i):
    RanaModule.__init__(self, m, d, i)
    self._layers = {}
    self._groups = {}
    # TODO: actually support runtime layer reconfiguration
    # and use this signal
    self.layersChanged = Signal()
    # parse the config file
    self._parseConfig()

  def getLayerById(self, layerId):
    """Get layer by Id
    :param layerId: map layer group ID
    :return: MapLayer object instance
    """
    return self._layers.get(layerId, None)

  def getLayersByIds(self, layerIds):
    """Get layer by Id
    :param layerIds: a list of map layer Ids
    :return: a list of MapLayer object instances
    """
    return filter(lambda x: x.id in layerIds, self._layers.values())

  def getLayersByGroupId(self, groupId):
    """Get layer by Id
    :param groupId: map layer group ID
    :return: MapLayer object instance
    """
    return filter(lambda x: x.groupId == groupId, self._layers.values())

  def getLayersWithoutGroup(self):
    """Map layers without group have their group id set to None
    :return: list o MapLayer instances that have no group set
    """
    return filter(lambda x: x.id is None, self._layers.values())

  def getLayerIds(self):
    """Get a list of all layer ids
    :return: a list of all layer ids
    :rtype: a list
    """
    return self._layers.keys()

  def getLayerList(self):
    """Get a list of all layers
    :return: a list of all layers
    :rtype: a list
    """
    return self._layers.values()

  def getLayerDict(self):
    """Get a dictionary of all layers
    :return: a dict of all layers
    :rtype: a dict
    """
    return self._layers

  def getGroupById(self, groupId):
    """Get group by Id
    :param groupId: map layer group ID
    :return: MapLayerGroup object instance
    """
    return self._groups.get(groupId, None)

  def getGroupList(self, sort=False):
    """Get a list off all known groups
    :param sort: if True, sort the groups by label alphabetically
    :return: a list of all groups
    """
    if sort:
      return sorted(self._groups.values(), key=lambda x: x.label)
    else:
      return self._groups.values()

  def _parseConfig(self):
    # check if there is at least one valid layer
    self._parseLayers()
    self._parseGroups()

  def _parseLayers(self):
    """Parse all map layer definitions"""
    # check if there is at least one valid layer

    layerDefinitions = self.modrana.configs.mapConfig.get('layers', {})
    for layerId, layerDefinition in layerDefinitions.iteritems():
      if self._hasRequiredKeys(layerDefinition, MAP_LAYER_REQUIRED_KEYS):
        self._layers[layerId] = MapLayer(layerId, layerDefinition)
      else:
        print('MapLAyers: layer %s definition is missing required keys')
    if self._layers == {}:
      print('MapLayers: map config has no valid layers,'
            ' using Mapnik fallback layer')
      self._layers['mapnik'] = self._getFallbackLayer()

  def _parseGroups(self):
    """Parse all map layer group definitions"""
    # as groups are not strictly needed for modRana
    # to show at least one map layer, we don't check if the
    # configuration file has any
    if self.modrana.configs.mapConfig:
      groupsDict = self.modrana.configs.mapConfig.get('groups', {})
      for groupId, groupDefinition in groupsDict.iteritems():
        if self._hasRequiredKeys(groupDefinition, MAP_LAYER_GROUP_REQUIRED_KEYS):
          self._groups[groupId] = MapLayerGroup(self, groupId, groupDefinition)

  def _getFallbackLayer(self):
    """In case that loading the map configuration
    file fails, this Mapnik layer can be used as a fallback.
    """
    return MapLayer(
      layerId="mapnik",
      config = {
        'label' :"OSM Mapnik",
        'url' : "http://c.tile.openstreetmap.org",
        'max_zoom' : 18,
        'min_zoom' : 0,
        'folder_prefix' : "OpenStreetMap I",
        'coordinates' : "osm"
      }
    )

  def _hasRequiredKeys(self, definition, requiredKeys):
    """Check if the layerDefinition has all keys specified that
    are required"""
    defSet = set(definition.keys())
    return requiredKeys <= defSet

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
    return int(self.config['max_zoom'])

  @property
  def minZoom(self):
    return int(self.config['min_zoom'])

  @property
  def folderName(self):
    return self.config['folder_prefix']

  @property
  def coordinates(self):
    return self.config['coordinates']

  @property
  def groupId(self):
    return self.config.get('group', None)

  @property
  def icon(self):
    return self.config.get('icon', None)

class MapLayerGroup(object):
  """A group of map layers"""
  def __init__(self, mapLayers, groupId, config, layerIds=None):
    """
    :param mapLayers : the mapLayers module
    :param groupId: unique map layer group identifier
    :param config: a dictionary with map layer configuration
    :param layerIds: a list of map layer identifiers that are part of the group
    """
    if not layerIds: layerIds = []
    self._mapLayers = mapLayers
    self._layers = []
    self._groupId = groupId
    self._config = config
    # load layers
    self._reloadLayers()
    # connect to the layer changed signal
    self._mapLayers.layersChanged.connect(self._reloadLayers)

  def _reloadLayers(self):
    """Reload map layers for this group from the mapLayers module"""
    self._layers = self._mapLayers.getLayersByGroupId(self.id)
    # sort the layers by the label
    # as that is what is usually needed when displaying them
    self._layers.sort(key=lambda l: l.label)

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
  def icon(self):
    return self._config.get('icon', None)

  @property
  def layers(self):
    return self._layers

  @property
  def layerIds(self):
    return map(lambda x: x.id, self._layers)