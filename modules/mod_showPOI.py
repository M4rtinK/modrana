# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Show POI on the map and in the menu.
#----------------------------------------------------------------------------
# Copyright 2010, Martin Kolman
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
from __future__ import with_statement # for python 2.5
from modules.base_module import RanaModule
from core import geo
from core.point import POI
from core.singleton import modrana
import math
import threading


def getModule(*args, **kwargs):
    return ShowPOI(*args, **kwargs)


class ShowPOI(RanaModule):
    """Show POI on the map and in the menu."""

    def __init__(self, *args, **kwargs):
        RanaModule.__init__(self, *args, **kwargs)
        self.activePOI = None
        self.visiblePOI = []
        self.listMenusDirty = True
        self.drawActivePOI = False
        self.expectPoint = False
        self.expectLock = threading.Lock()

    def firstTime(self):
        # restore the IDs of visible POI
        self.restoreVisibleIDs()

    def handleMessage(self, message, messageType, args):
        # messages that need the store and/or menus go here
        store = self.m.get('storePOI', None)
        menus = self.m.get('menu', None)
        if store and menus:
            if message == "setupCategoryList":
                if messageType == 'ml':
                    # this is used for executing something special instead of going to the POIDetail menu
                    # after a POI is selected
                    POISelectedAction = args[0]
                    action = "ml:showPOI:setupPOIList:%s;%s|set:menu:menu#list#POIList" % ("%d", POISelectedAction)
                else:
                    action = "ms:showPOI:setupPOIList:%d|set:menu:menu#list#POIList"
                usedCategories = store.db.list_used_categories()
                # convert cat_id to actions
                i = 0
                for item in usedCategories:
                    (label, desc, cat_id) = item
                    buttonAction = action % cat_id
                    usedCategories[i] = (label, desc, buttonAction)
                    i += 1
                menus.addListMenu('POICategories', "set:menu:poi", usedCategories)
            elif message == 'setupPOIList':
                if args:
                    catId = None
                    action = "set:menu:None"
                    if messageType == 'ms':
                        catId = int(args)
                        action = 'set:menu:showPOI#POIDetail' # use the default action
                    elif messageType == 'ml':
                        # if the message is a message list, execute a custom action instead of the default POI detail menu
                        # TODO: use this even for selecting the POIDetail menu ?
                        catId = int(args[0])
                        action = args[1]
                    if catId is not None:
                        poiFromCategory = store.db.get_all_poi_from_category(catId)
                    else:
                        poiFromCategory = []
                    # convert the output to a listable menu compatible state
                    i = 0
                    for item in poiFromCategory:
                        (label, _desc, lat, lon, poi_id) = item
                        subText = "lat: %f, lon: %f" % (lat, lon)
                        buttonAction = "ms:showPOI:setActivePOI:%d|%s" % (poi_id, action)
                        poiFromCategory[i] = (label, subText, buttonAction)
                        i += 1
                    menus.addListMenu("POIList", 'set:menu:menu#list#POICategories', poiFromCategory)
            elif messageType == 'ms' and message == 'setActivePOI':
                if args:
                    POIId = int(args)
                    self.activePOI = GTKPOI(store.db.get_poi(POIId))
            elif messageType == 'ms' and message == 'storePOI':
                if args == "manualEntry":
                    # add all POI info manually
                    entry = self.m.get('textEntry', None)
                    if entry:
                        self.activePOI = GTKPOI(store.getEmptyPOI())  # set a blank POI as active
                        # start the chain of entry boxes
                        entry.entryBox(self, 'newName', 'POI name', "")
                elif args == "currentPosition":
                    # add current position as a new POI
                    entry = self.m.get('textEntry', None)
                    if entry:
                        pos = self.get('pos', None)
                        if pos:
                            self.activePOI = GTKPOI(store.getEmptyPOI()) # set a blank POI as active
                            (lat, lon) = pos
                            self.activePOI.lat = lat
                            self.activePOI.lon = lon
                            # start the entry box chain
                            entry.entryBox(self, 'newCurrentPositionName', 'POI name', "")
                elif args == "fromMap":
                    with self.expectLock: # nobody expects a lock here
                        self.expectPoint = True # turn on registering the whole screen clickable
                    self.set('menu', None)
                    self.sendMessage('ml:notification:m:Tap on the map to add POI;3')
                elif args == "fromMapDone": # this is after the point has been clicked
                    with self.expectLock:
                        if self.expectPoint == True:
                            self.expectPoint = False # disable the registering
                            proj = self.m.get('projection', None)
                            lastClick = self.get('lastClickXY', None)
                            entry = self.m.get('textEntry', None)
                            if proj and lastClick and entry:
                                (x, y) = lastClick
                                (lat, lon) = proj.xy2ll(x, y)
                                self.activePOI = GTKPOI(store.getEmptyPOI()) # set a blank POI as active
                                self.activePOI.lat = lat
                                self.activePOI.lon = lon
                                # start the entry box chain
                                # we misuse the current position chain
                                entry.entryBox(self, 'newCurrentPositionName', 'POI name', "")

            elif messageType == 'ms' and message == 'editActivePOI':
                entry = self.m.get('textEntry', None)
                if args:
                    if entry:
                        if args == 'name':
                            name = self.activePOI.name
                            entry.entryBox(self, 'name', 'POI name', name)
                        if args == 'description':
                            description = self.activePOI.description
                            entry.entryBox(self, 'description', 'POI Description', description)
                        if args == 'lat':
                            lat = str(self.activePOI.lat)
                            entry.entryBox(self, 'lat', 'POI Latitude', lat)
                        if args == 'lon':
                            lon = str(self.activePOI.lon)
                            entry.entryBox(self, 'lon', 'POI Longitude', lon)

            elif messageType == 'ml' and message == 'setupPOICategoryChooser':
                # setup a category chooser menu
                if args:
                    (menu, key) = args
                    self._setupPOICategoryChooser(menu, key)

            elif messageType == 'ms' and message == 'setCatAndCommit':
                # selecting the category is the final stage of adding a POI
                if args:
                    # set the category index
                    self.activePOI.db_category_index = int(args)
                    # commit the new POI to db
                    self.activePOI.commit()
                    # mark list menus for regeneration
                    self.listMenusDirty = True
                    # go to the new POI menu
                    self.set('menu', 'showPOI#POIDetail')

            elif message == 'checkMenus':
                # check if the POI menus are "dirty" and need to be regenerated
                if self.listMenusDirty:
                    self.sendMessage('showPOI:setupCategoryList')
                    if self.activePOI:
                        catId = self.activePOI.db_category_index
                        self.sendMessage('ms:showPOI:setupPOIList:%d' % catId)
                    self.listMenusDirty = False

            elif message == "updateToolsMenu":
                self.activePOI.updateToolsMenu()

            elif message == 'listMenusDirty':
                # something regarding the POI changed
                # ,the menus might not be up to date
                # and may need a regen
                self.listMenusDirty = True

            elif message == 'askDeleteActivePOI':
                ask = self.m.get('askMenu', None)
                if ask:
                    id = self.activePOI.db_index
                    name = self.activePOI.name
                    question = "Do you really want to delete:\n%s\nfrom the POI database ?" % name
                    yesAction = "ms:storePOI:deletePOI:%d|set:menu:menu#list#POICategories" % id
                    noAction = "showPOI:updateToolsMenu|set:menu:POIDetailTools"
                    ask.setupAskYesNo(question, yesAction, noAction)

            elif message == 'centerOnActivePOI':
                # something regarding the POI changed
                # ,the menus might not be up to date
                # and may need a regen"""
                self.activePOI.showOnMap()

            elif message == 'routeToActivePOI':
                # something regarding the POI changed
                # ,the menus might not be up to date
                # and may need a regen"""
                self.activePOI.routeFrom('currentPosition')
                self.sendMessage('mapView:recentreToPos')
                self.makePOIVisible(self.activePOI)
                self.drawPOI()
                self.set('menu', None)

            elif message == 'drawActivePOI':
                if self.activePOI: # only add valid poi
                    self.makePOIVisible(self.activePOI)
                    # enable drawing
                    self.drawPOI()

            elif message == 'dontDrawActivePOI':
                self.removePOIFromVisible(self.activePOI)

            elif message == 'makeAllStoredPOIVisible':
                count = self.makeAllStoredPOIVisible()
                self.set("menu", None)
                self.notify("All %d stored POI are now visible" % count, 2000)

            elif message == 'clearVisiblePOI':
                count = self.clearVisiblePOI()
                if count > 0:
                    self.notify("%d visible POI cleared" % count, 2000)
                else:
                    self.notify("Nothing to clear", 2000)

    def makePOIVisible(self, POI):
        """add a POI to the list of visible POI & save ID"""
        self._makePOIVisible(POI)
        self.saveVisibleIDs()

    def _makePOIVisible(self, POI):
        """add a POI to the list of visible POI & don't save ID"""
        # check if the POI is already present
        if POI and POI not in self.visiblePOI:
            self.visiblePOI.append(POI)

    def makeAllStoredPOIVisible(self):
        """make all stored POI visible"""
        store = self.m.get('storePOI', None)
        cats = store.db.list_categories()
        count = 0
        _makePOIVisible = self._makePOIVisible
        for cat in cats:
            (label, desc, cat_id) = cat
            catPOI = store.db.get_all_poi_from_category(cat_id)
            count += len(catPOI)
            for item in catPOI:
                (label, _desc, lat, lon, poi_id) = item
                _makePOIVisible(store.db.get_poi(poi_id))
        self.saveVisibleIDs()
        self.drawPOI()
        return count

    def clearVisiblePOI(self):
        """discard visible POI"""
        count = len(self.visiblePOI)
        self.dontDrawPOI()
        self.visiblePOI = []
        self.saveVisibleIDs()
        return count

    def removePOIFromVisible(self, POI):
        if POI in self.visiblePOI:
            self.visiblePOI.remove(POI)
            self.saveVisibleIDs()

    def saveVisibleIDs(self):
        visibleIDs = []
        for POI in self.visiblePOI:
            visibleIDs.append(POI.db_index)
        self.set("visiblePOIIDs", visibleIDs)

    def restoreVisibleIDs(self):
        visibleIDs = self.get("visiblePOIIDs", [])
        if visibleIDs:
            store = self.m.get('storePOI', None)
            if store:
                for poiID in visibleIDs:
                    self._makePOIVisible(store.db.get_poi(poiID))
                if self.visiblePOI: # enable POI drawing only if some POI vere restored
                    self.drawPOI()
                self.log.info("showPOI: %d visible POI restored", len(self.visiblePOI))
            else:
                self.log.error("showPOI: can't restore visible, the storePOI module is not loaded")
