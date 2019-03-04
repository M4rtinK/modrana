# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# A modRana module for map layer handling
#----------------------------------------------------------------------------
# Copyright 2013, Martin Kolman
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
import os
import sys
import traceback

from modules.base_module import RanaModule
from core.signal import Signal
from core.backports import six
from core.layers import MapLayer, MapLayerGroup
from .overlay_groups import OverlayGroup

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


def getModule(*args, **kwargs):
    return MapLayers(*args, **kwargs)


class MapLayers(RanaModule):
    """Map layer handling"""

    def __init__(self, *args, **kwargs):
        RanaModule.__init__(self, *args, **kwargs)
        self._layers = {}
        self._groups = {}
        self._tree = {}
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
        return filter(lambda x: x.group_id == groupId, self._layers.values())

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

    def getDictOfLayerDicts(self):
        """Get a dictionary of all layers dicts
        (each layer is represented by its dictionary
        representation)

        :return: a dict of all layer dictionaries
        :rtype: a dict
        """
        d = {}
        for k, v in self._layers.items():
            d[k] = v.dict
        return d

    def getLayerTree(self):
        """Get a tree representation of the groups and layers,
        a list of group dicts is returned and each group dict
        has a list of layer dicts

        :returns: list of dicts
        :rtype: list
        """
        if not self._tree:
            self._tree = [g.dict for g in self.getGroupList(sort=True)]
        return self._tree

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

        layerDefinitions = self.modrana.configs.map_config.get('layers', {})
        for layerId, layerDefinition in six.iteritems(layerDefinitions):
            if self._hasRequiredKeys(layerDefinition, MAP_LAYER_REQUIRED_KEYS):
                self._layers[layerId] = MapLayer(layerId, layerDefinition)
            else:
                self.log.error('layer %s definition is missing required keys', layerId)
        if self._layers == {}:
            self.log.error('map layer config has no valid layers,'
                           ' using Mapnik fallback layer')
            self._layers['mapnik'] = self._getFallbackLayer()

    def _parseGroups(self):
        """Parse all map layer group definitions"""
        # as groups are not strictly needed for modRana
        # to show at least one map layer, we don't check if the
        # configuration file has any
        if self.modrana.configs.map_config:
            groupsDict = self.modrana.configs.map_config.get('groups', {})
            for groupId, groupDefinition in six.iteritems(groupsDict):
                if self._hasRequiredKeys(groupDefinition, MAP_LAYER_GROUP_REQUIRED_KEYS):
                    self._groups[groupId] = MapLayerGroup(self, groupId, groupDefinition)

    def _getFallbackLayer(self):
        """In case that loading the map configuration
        file fails, this Mapnik layer can be used as a fallback.
        """
        return MapLayer(
            layerId="mapnik",
            config={
                'label': "OSM Mapnik",
                'url': "http://c.tile.openstreetmap.org",
                'max_zoom': 18,
                'min_zoom': 0,
                'folder_prefix': "OpenStreetMap I",
                'coordinates': "osm"
            }
        )

    def _hasRequiredKeys(self, definition, requiredKeys):
        """Check if the layerDefinition has all keys specified that
        are required"""
        defSet = set(definition.keys())
        return requiredKeys <= defSet

    # overlays

    def getOverlayGroupNames(self):
        """Return available overlay group names
        NOTE: overlay group names are equal to the names of the JSON
              files used to store the groups, minus the .json suffix
              -> like this we don't actually have to parse all the JSONs
                 to get a list of all available groups

        :returns: list of available overlay group names
        :rtype: list
        """
        candidates = os.listdir(self.modrana.paths.overlay_groups_folder_path)
        return [n[0:-5] for n in candidates if n.endswith(".json")]

    def getOverlayGroup(self, name):
        filename = "%s.json" % name
        filePath = os.path.join(self.modrana.paths.overlay_groups_folder_path, filename)
        if os.path.isfile(filePath):
            return OverlayGroup(name, filePath)
        else:
            return None

    def getOverlayGroupAsList(self, name):
        """A convenience function for getting just the list
        of overlays corresponding to the overlay group specified
        by the given name
        """
        group = self.getOverlayGroup(name)
        if group:
            return group.overlays
        else:
            return None

    def setOverlayGroup(self, name, overlayList):
        filename = "%s.json" % name
        filePath = os.path.join(self.modrana.paths.overlay_groups_folder_path, filename)
        try:
            # the overlay group automatically saves any changes to persistent
            # storage so we don't have to explicitly call save() on it here
            OverlayGroup(name, filePath, overlayList=overlayList)
        except Exception:
            self.log.exception("setting overlay group %s failed", name)
            self.log.error("current overlay list:")
            self.log.error(overlayList)
