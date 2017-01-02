# Map layer representation classes

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

    @property
    def timeout(self):
        return self.config.get('timeout', None)

    @property
    def dict(self):
        """ Return a dictionary representing the layer

        :returns: dictionary representation of the layer
        :rtype: dict
        """
        return {
            "id" : self.id,
            "label" : self.label,
            "url" : self.url,
            "type" : self.type,
            "maxZoom" : self.maxZoom,
            "minZoom" : self.minZoom,
            "folderName" : self.folderName,
            "coordinates" : self.coordinates,
            "groupId" : self.groupId,
            "icon" : self.icon,
            "timeout" : self.timeout
        }

    def __repr__(self):
        return "%s layer" % self.id


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
        self._layers = sorted(self._layers, key=lambda l: l.label)

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

    @property
    def dict(self):
        """ Return a dictionary representing the layer group,
        including a list of dictionary for all layers in the group

        :returns: dictionary representation of the layer group
        :rtype: dict
        """
        return {
            "id" : self.id,
            "label" : self.label,
            "icon" : self.icon,
            "layers" : [l.dict for l in self._layers],
        }