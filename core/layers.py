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
        """Unique map layer indicator.

        :return: unique map layer identifier
        """
        return self._layerId

    @property
    def label(self):
        """Human readable name of the ma layer.

        :returns: human readable name
        :rtype: str
        """
        return self.config['label']

    @property
    def url(self):
        """Map layer URL.

        :returns: map layer URL
        :rtype: str
        """
        return self.config['url']

    @property
    def type(self):
        """Map layer type.

        :returns: map layer type
        """
        return self.config['type']

    @property
    def max_zoom(self):
        """Maximum zoom level.

        :returns: maximum zoom level
        :rtype: int
        """
        return int(self.config['max_zoom'])

    @property
    def min_zoom(self):
        """Minimum zoom level.

        :returns: minimum zoom level
        :rtype: int
        """
        return int(self.config['min_zoom'])

    @property
    def folder_name(self):
        """Name of the folder for storing the tiles.


        :returns: map layer folder name
        :rtype: str
        """
        return self.config['folder_prefix']

    @property
    def coordinates(self):
        """Layer coordinate type.

        :returns: layer coordinate type
        :rtype: str
        """
        return self.config['coordinates']

    @property
    def group_id(self):
        """Parent layer group id.

        :returns: parent layer group id
        :rtype: str
        """
        return self.config.get('group', None)

    @property
    def icon(self):
        """Layer icon name.

        Has to be a name of an icon modRana has available locally.

        :returns: layer icon name
        :rtype: str
        """
        return self.config.get('icon', None)

    @property
    def timeout(self):
        """How long should tiles be considered current.

        Tiles that are no longer considered current will be downloaded again
        instead of being loaded from storage.

        :returns: tile storage timeout (in hours)
        :rtype: float or None
        """
        tile_timeout = self.config.get('timeout', None)
        if tile_timeout is not None:
            return float(tile_timeout)
        else:
            return tile_timeout

    @property
    def connection_timeout(self):
        """How long should we wait for tile to be download for this layer.
        
        This can be of a bigger importance for local host tile rendering
        servers that might take longer to render a tile but unlike a remote
        tile server that might never reply due to connection interruption
        the local rendering tileserver should almost always eventually
        send back the tile.

        :returns: connection timeout (in seconds)
        :rtype: int or None
        """
        tile_connection_timeout = self.config.get('connection_timeout', None)
        if tile_connection_timeout is not None:
            return int(tile_connection_timeout)
        else:
            return tile_connection_timeout


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
            "max_zoom" : self.max_zoom,
            "min_zoom" : self.min_zoom,
            "folder_name" : self.folder_name,
            "coordinates" : self.coordinates,
            "group_id" : self.group_id,
            "icon" : self.icon,
            "timeout" : self.timeout,
            "connection_timeout" : self.connection_timeout
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
        self._reload_layers()
        # connect to the layer changed signal
        self._mapLayers.layersChanged.connect(self._reload_layers)

    def _reload_layers(self):
        """Reload map layers for this group from the mapLayers module"""
        # TODO: move the layer loading code here
        self._layers = self._mapLayers.getLayersByGroupId(self.id)
        # sort the layers by the label
        # as that is what is usually needed when displaying them
        self._layers = sorted(self._layers, key=lambda l: l.label)

    @property
    def id(self):
        """Unique map layer group id.

        :returns: unique map layer group identifier
        :rtype: str
        """
        return self._groupId

    @property
    def label(self):
        """Layer icon name.

        Has to be a name of an icon modRana has available locally.

        :returns: icon name
        :rtype: str
        """
        return self._config['label']

    @property
    def icon(self):
        """Layer group icon name.

        Has to be a name of an icon modRana has available locally.

        :returns: layer group icon name
        :rtype: str
        """
        return self._config.get('icon', None)

    @property
    def layers(self):
        """List of contained layers.

        :returns: list of contained layers
        :rtype: list of layer instances
        """
        return self._layers

    @property
    def layer_ids(self):
        """Map layer ids of contained map layers.

        :returns: map layer ids of contained map layers
        :rtype: iterable of strings
        """
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