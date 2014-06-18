# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# modRana theming support
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
from modules.base_module import RanaModule

from core.signal import Signal
from core.backports import six

# for some reason one import method works
# on Fremantle and other everywhere (?) else"""
try:
    from configobj import ConfigObj # everywhere
except Exception:
    import sys

    e = sys.exc_info()[1]
    print(e)
    print("theme: trying alternative configobj import method")
    from configobj import ConfigObj # Fremantle

THEME_CONFIG_FILENAME = "theme.conf"


def getModule(m, d, i):
    return ThemeModule(m, d, i)


class ThemeModule(RanaModule):
    """ModRana theming module"""

    def __init__(self, m, d, i):
        RanaModule.__init__(self, m, d, i)
        self._themeChanged = Signal()

        self.modrana.watch('theme', self._themeChangedCB, runNow=True)

    @property
    def themeChanged(self):
        """Theme changed signal
        :returns: instance of the theme changed signal"""
        return self._themeChanged

    @property
    def theme(self):
        """Current theme
        :returns: current theme
        :rtype: Theme
        """
        return self._theme

    def _getThemesPath(self):
        return self.modrana.paths.getThemesFolderPath()

    def _themeChangedCB(self, key, oldValue, newValue):
        """Triggered by theme change"""
        if newValue is None: # default theme
            defaultThemeId, defaultThemeName = self.modrana.dmod.defaultTheme
            self._theme = Theme(defaultThemeId, self._getThemesPath(), defaultThemeName)
        else: # set the new theme
            self._theme = Theme(newValue, self._getThemesPath())
            self._themeChanged(self._theme)  # fire the theme changed signal

    def getAvailableThemeIds(self):
        """Return a a list of currently available themes (list of folders in the themes folder)
        :returns: a list of available theme ids
        :rtype: a list of strings
        """
        rawFolderContent = os.listdir(self.modrana.paths.getThemesFolderPath())
        # append the full path and filter out all dot-folders, such as .svn, .git & co
        themesFolderPath = self.modrana.paths.getThemesFolderPath()
        return filter(
            lambda x: os.path.isdir(
                os.path.join(themesFolderPath, x)) and not x.startswith('.'),
            rawFolderContent
        )


class Theme(object):
    """A modRana theme"""

    def __init__(self, themeId, themesPath, name=None):
        self._id = themeId
        if name is None:
            name = themeId

        self._name = name
        # for now just color_name : color_string
        self._colors = {}

        # load the theme config file
        path = os.path.join(themesPath, themeId, THEME_CONFIG_FILENAME)
        self._loadConfigFile(path)


    def __repr__(self):
        return "id: %s, name: %s, %d colors" % (self._id, self._name, len(self._colors))

    @property
    def id(self):
        """
        :returns: unique theme id
        :rtype: string
        """
        return self._id

    @property
    def name(self):
        """
        :returns: name of the theme
        :rtype: string
        """
        return self._name

    def getColor(self, key, default):
        return self._colors.get(key, default)

    def _loadConfigFile(self, path):
        """load color definitions from file"""

        config = ConfigObj(path)

        # try to get theme name from the config
        try:
            name = config['theme']['name']
            if name:
                self._name = name
        except KeyError:
            pass

        # load color definitions
        if 'colors' in config:
            colors = config['colors']
            colorObjects = {}
            for key, color in six.iteritems(colors):
                if len(color) == 2: # hex color/color name and alpha as float 0-1
                    colorString = color[0]
                    colorObjects[key] = colorString
                    # TODO: alpha support, other formats
                    # TODO: use the Color object
            self._colors = colorObjects
        else:
            self._colors = {}












