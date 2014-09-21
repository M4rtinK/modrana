# -*- coding: utf-8 -*-
# Overlay group classes

from core import json_dict

OVERLAYS_KEY = "overlays"
OVERLAY_GROUP_DICT_TEMPLATE = {OVERLAYS_KEY : {}}

class Overlay(object):
    """ A map overlay
    NOTE: even the overlay that is actually the base layer
          is classified as an overlay and can be semi-/transparent

    NOTE: not actually used at the moment as we get the overlay list
          directly from the QML context
    """

    def __init__(self, layer, opacity):
        self._layer = layer
        self._opacity = opacity

    @property
    def label(self):
        return self._layer.label

    @property
    def layerId(self):
        return self._layer.id

    @property
    def layer(self):
        return self._layer

    @property
    def opacity(self):
        return self._opacity


class OverlayGroup(object):
    """ An ordered group of map Overlays,
    the first overlay is the base layer and the subsequent
    overlays are the actual overlays
    """

    def __init__(self, name, filePath, overlayList=None, autosave=True):
        self._name = name
        self._autosave = autosave
        if overlayList:
            overlayDict = OVERLAY_GROUP_DICT_TEMPLATE
            overlayDict[OVERLAYS_KEY] = overlayList
            # if JSONDict gets a dict, it uses it as its source,
            # if it does not get a dict but gets a path, it tries to
            # load itself from the path
            # * so if we want to save something, we provide both
            # * and when we want to load something, we provide only the path
            self._dict = json_dict.JSONDict(filePath=filePath, dictionary=overlayDict)
        else:
            self._dict = json_dict.JSONDict(filePath=filePath)

        if autosave:
            self.save()

    @property
    def name(self):
        return self._name

    @property
    def overlays(self):
        return self._dict.get(OVERLAYS_KEY, [])

    @overlays.setter
    def overlays(self, overlayList):
        self._dict[OVERLAYS_KEY] = overlayList
        if self._autosave:
            self.save()

    def save(self):
        """ Save the overlays into a JSON file on persistent storage"""
        self._dict.save()