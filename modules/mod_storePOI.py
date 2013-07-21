# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Store POI data.
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
import traceback
import sys
from modules.base_module import RanaModule
import os
import sqlite3
import csv
from core.backports.six import u


def getModule(m, d, i):
    return StorePOI(m, d, i)


class StorePOI(RanaModule):
    """Store POI data."""

    def __init__(self, m, d, i):
        RanaModule.__init__(self, m, d, i)
        self.db = None
        self.tempOnlinePOI = None # temporary slot for an uncommitted POI from online search
        # to which menu to return after the POI is stored
        # NOTE: False => unset, None => map screen
        self.menuNameAfterStorageComplete = False
        # connect to the POI database
        self.connectToDb()

    def firstTime(self):
        self.checkImport() # check if there ary any old POI to import

    def connectToDb(self):
        """connect to the database"""
        DBPath = self.modrana.paths.getPOIDatabasePath()
        if os.path.exists(DBPath): # connect to db
            print(" @ storePOI: POI database path:\n @ %s" % DBPath)
            try:
                self.db = sqlite3.connect(DBPath)
                print(" @ storePOI: connection to POI db established")
            except Exception:
                import sys

                e = sys.exc_info()[1]
                print(" @ storePOI: connecting to POI database failed:\n%s" % e)
        else: # create new db
            try:
                self.db = self.createDatabase(DBPath)
            except Exception:
                import sys

                e = sys.exc_info()[1]
                print(" @ storePOI: creating POI database failed:\n%s" % e)

    def disconnectFromDb(self):
        print("storePOI: disconnecting from db")
        if self.db:
            self.db.close()

    def createDatabase(self, path):
        """create a new database, including tables and initial data
        return the connection object"""
        print("storePOI: creating new database file in:\n%s" % path)
        conn = sqlite3.connect(path)

        # create the category table
        conn.execute('CREATE TABLE category (cat_id integer PRIMARY KEY,label text, desc text, enabled integer)')
        # create the poi table
        conn.execute(
            'CREATE TABLE poi (poi_id integer PRIMARY KEY, lat real, lon real, label text, desc text, cat_id integer)')
        # load the predefined categories
        # (currently the same ones as in MaemoMapper)
        defaultCats = [(1, u('Service Station'), u('Stations for purchasing fuel for vehicles.'), 1),
                       (2, u('Residence'), u('Houses, apartments, or other residences of import.'), 1),
                       (3, u('Restaurant'), u('Places to eat or drink.'), 1),
                       (4, u('Shopping/Services'), u('Places to shop or acquire services.'), 1),
                       (5, u('Recreation'), u('Indoor or Outdoor places to have fun.'), 1),
                       (6, u('Transportation'), u('Bus stops, airports, train stations, etc.'), 1),
                       (7, u('Lodging'), u('Places to stay temporarily or for the night.'), 1),
                       (8, u('School'), u('Elementary schools, college campuses, etc.'), 1),
                       (9, u('Business'), u('General places of business.'), 1),
                       (10, u('Landmark'), u('General landmarks.'), 1),
                       (11, u('Other'), u('Miscellaneous category for everything else.'), 1)]
        for cat in defaultCats:
            conn.execute('insert into category values(?,?,?,?)', cat)
            # commit the changes
        conn.commit()
        print("storePoi: new database file has been created")
        return conn

    def storePOI(self, POI):
        """store a POI object to the database"""
        if self.db:
            values = POI.getDbOrder()
            query = "replace into poi values(?,?,?,?,?,?)"
            self.db.execute(query, values)
            self.db.commit()

    def deletePOI(self, poiId):
        """delete a poi with given ID from the database"""
        self.db.execute('delete from poi where poi_id=?', [poiId])
        self.db.commit()

    def getCategories(self):
        """return a list of all available categories"""
        if self.db:
            return self.db.execute('select label,desc,cat_id from category').fetchall()

    def getUsedCategories(self):
        """return list of categories that have at least one POI"""
        if self.db:
            # find which POI categories are actually used
            # TODO: investigate how this scales for many points
            usedCatIds = self.db.execute('select distinct cat_id from poi').fetchall()
            usedCategories = []
            for catId in usedCatIds:
                nameDescription = self.db.execute('select label,desc,cat_id from category where cat_id=?',
                                                  catId).fetchone()
                if nameDescription:
                    usedCategories.append(nameDescription)
            return usedCategories #this should be a list of used category ids
        else:
            return None

    def getCategoryForId(self, catId):
        """return cat_id,label, desc, enabled from a given cat_id"""
        result = self.db.execute('select cat_id,label,desc,enabled from category where cat_id=?', [catId]).fetchone()
        return result

    def getAllPOIFromCategory(self, catId):
        """return a list of POI from a given category"""
        if self.db:
            result = self.db.execute('select label,lat,lon,poi_id from poi where cat_id=?', [catId]).fetchall()
            return result
        else:
            return None

    def getPOI(self, POIId):
        """return a complete POI row from db fow a given POI Id"""
        if self.db:
            result = self.db.execute('select poi_id, lat, lon, label, desc, cat_id from poi where poi_id=?',
                                     [POIId]).fetchone()
            if result:
                (poi_id, lat, lon, label, desc, cat_id) = result
                # make it more usable
                POIObject = self.POI(self, label, desc, lat, lon, cat_id, poi_id)
                return POIObject
            else:
                return None
        else:
            return None

    class POI(object):
        """This class represents a POI"""

        def __init__(self, callback, label, description, lat, lon, catId, poiId=None):
            self.callback = callback
            self.id = poiId
            self.lat = lat
            self.lon = lon
            self.label = u('%s') % label
            self.description = u('%s') % description
            self.categoryId = catId

        def __str__(self):
            s = "POI named: %s, lat,lon: %f,%f with id: %d" % (
            self.getName(), self.getLat(), self.getLon(), self.getId())
            return s

        def __eq__(self, other):
            return self.getId() == other.getId()

        def getMenus(self):
            """convenience function for getting the menus object"""
            return self.callback.m.get('menu', None)

        def getId(self):
            return self.id

        def getLat(self):
            return self.lat

        def getLon(self):
            return self.lon

        def getName(self):
            return self.label

        def getDescription(self):
            return self.description

        def getCatId(self):
            return self.categoryId

        def getDbOrder(self):
            """get the variables in the order, they are stored in the database"""
            return (
                self.getId(),
                self.getLat(),
                self.getLon(),
                self.getName(),
                self.getDescription(),
                self.getCatId()
            )

        def drawMenu(self, cr):
            menus = self.getMenus()
            if menus:
                button1 = ('map#show on', 'generic',
                           'mapView:recentre %f %f|showPOI:drawActivePOI|set:menu:None' % (self.lat, self.lon))
                button2 = ('tools', 'tools', 'showPOI:updateToolsMenu|set:menu:POIDetailTools')
                if self.label is not None and self.lat is not None and self.lon is not None and self.description is not None:
                    text = "<big><b>%s</b></big>\n\n%s\n\nlat: <b>%f</b> lon: <b>%f</b>" % (
                    self.label, self.description, self.lat, self.lon)
                else:
                    text = "POI is being initialized"
                box = (text, '')
                menus.drawThreePlusOneMenu(cr, 'POIDetail', 'showPOI:checkMenus|set:menu:menu#list#POIList', button1,
                                           button2, box, wrap=True)

        def updateToolsMenu(self):
            # setup the tools submenu
            menus = self.getMenus()
            if menus:
                menus.clearMenu('POIDetailTools', "set:menu:showPOI#POIDetail")
                menus.addItem('POIDetailTools', 'here#route', 'generic', 'showPOI:routeToActivePOI')
                menus.addItem('POIDetailTools', 'name#edit', 'generic', 'ms:showPOI:editActivePOI:name')
                menus.addItem('POIDetailTools', 'description#edit', 'generic', 'ms:showPOI:editActivePOI:description')
                menus.addItem('POIDetailTools', 'latitude#edit', 'generic', 'ms:showPOI:editActivePOI:lat')
                menus.addItem('POIDetailTools', 'longitude#edit', 'generic', 'ms:showPOI:editActivePOI:lon')
                menus.addItem('POIDetailTools', 'category#change', 'generic',
                              'ml:showPOI:setupPOICategoryChooser:showPOI;setCatAndCommit|set:menu:menu#list#POICategoryChooser')
                menus.addItem('POIDetailTools', 'position#set as', 'generic',
                              'showPOI:centerOnActivePOI|ml:location:setPosLatLon:%f;%f' % (self.lat, self.lon))
                # just after the point is stored and and its detail menu shows up for the first time,
                # it cant be deleted from the database, because we don't know which index it got :D
                # TODO: find a free index and then store the point on it
                # (make sure no one writes to the database between getting the free index and writing the poi to it)
                # then we would be able to delete even newly created points
                if self.getId():
                    menus.addItem('POIDetailTools', 'POI#delete', 'generic', 'showPOI:askDeleteActivePOI')

        def getValues(self):
            return [self.id, self.lat, self.lon, self.label, self.description, self.categoryId]

        def setName(self, newLabel, commit=True):
            self.label = u('%s') % newLabel
            if commit:
                self.storeToDb()

        def setDescription(self, newDescription, commit=True):
            self.description = u('%s') % newDescription
            if commit:
                self.storeToDb()

        def setLat(self, lat, commit=True):
            self.lat = float(lat)
            if commit:
                self.storeToDb()

        def setLon(self, lon, commit=True):
            self.lon = float(lon)
            if commit:
                self.storeToDb()

        def setCategory(self, newCatId, commit=True):
            self.categoryId = newCatId
            if commit:
                self.storeToDb()

        def storeToDb(self):
            """store this POI object to the database"""
            self.callback.storePOI(self)

        def showOnMap(self):
            """recentre to this POI and active point and label drawing"""
            self.callback.sendMessage(
                'mapView:recentre %f %f|showPOI:drawActivePOI|set:menu:None' % (self.lat, self.lon))

        def routeFrom(self, fromWhere):
            if fromWhere == 'currentPosition': # route from current position to this POI
                pos = self.callback.get('pos', None)
                if pos:
                    (fromLat, fromLon) = pos
                    # clear old route and route to the point
                    self.callback.sendMessage(
                        'route:clearRoute|md:route:route:type=ll2ll;fromLat=%f;fromLon=%f;toLat=%f;toLon=%f;' % (
                        fromLat, fromLon, self.getLat(), self.getLon()))

    def getEmptyPOI(self):
        """get a POI with all variables set to None"""
        POIObject = self.POI(self, None, None, None, None, None, None)
        return POIObject

    def checkImport(self):
        """check if there are any POI in the old format
           and try to import them to the db (into the "other" category)
           then rename the old poi file to prevent multiple imports"""

        oldPOIPath = "data/poi/poi.txt"
        if os.path.exists(oldPOIPath):
            try:
                renamedOldPOIPath = "data/poi/imported_old_poi.txt"
                print("storePOI:importing old POI from: %s" % oldPOIPath)
                points = self.loadOld(oldPOIPath)
                if points:
                    for point in points:
                        # create a new POI object
                        label = point.name
                        description = point.description.replace('|', '\n')
                        lat = point.lat
                        lon = point.lon
                        catId = 11
                        newPOI = self.POI(self, label, description, lat, lon, catId)
                        newPOI.storeToDb()
                    print("storePOI: imported %d old POI" % len(points))
                    os.rename(oldPOIPath, renamedOldPOIPath)
                    print("storePOI: old POI file moved to: %s" % renamedOldPOIPath)
                    self.sendMessage('ml:notification:m:%d old POI imported to category "Other";10' % len(points))
            except Exception:
                import sys

                e = sys.exc_info()[1]
                print("storePOI: import of old POI failed:\n%s" % e)


    def loadOld(self, path):
        """load POI from file - depreciated, used sqlite for POI storage"""
        try:
            f = open(path, 'r')
            import pickle

            points = pickle.load(f)
            f.close()
            return points
        except Exception:
            import sys

            e = sys.exc_info()[1]
            print("storePOI: loading POI from file failed:\n%s" % e)
            return None

    def handleMessage(self, message, messageType, args):
        if messageType == 'ms' and message == 'deletePOI':
            # remove a poi with given id from database
            if args:
                poiId = int(args)
                self.deletePOI(poiId) # remove the poi from database
                # notify the showPOI module, that it might need to rebuild its menus
                self.sendMessage('showPOI:listMenusDirty')
        elif messageType == 'ms' and message == 'setCatAndCommit':
            # set category and as this is the last needed input,
            # commit the new POI to db"""
            catId = int(args)
            # set the category to the one the user just selected
            self.tempOnlinePOI.setCategory(catId, commit=False)
            # commit the new online result based POI to db
            self.tempOnlinePOI.storeToDb()
            # signal that the showPOI menus may need to be regenerated
            self.sendMessage('showPOI:listMenusDirty')
            catInfo = self.getCategoryForId(catId)
            catName = catInfo[1]
            POIName = self.tempOnlinePOI.getName()
            # NOTE: False means the the variable is unset, as None means the map screen
            if self.menuNameAfterStorageComplete == False:
                self.set('menu', 'search#searchResultsItem')
            else:
                self.set('menu', self.menuNameAfterStorageComplete)

            self.sendMessage('ml:notification:m:%s has been saved to %s;5' % (POIName, catName))

        elif message == "reconnectToDb":
            # this means, that we need to reconnect the database connection
            # * this is used for example as a notification,
            # that the user changed the default POI db path"""
            self.disconnectFromDb()
            self.connectToDb()

        elif message == "dumpToCSV":
            # dump db to CSV file
            self.set('menu', None)
            self.dumpToCSV()

    def handleTextEntryResult(self, key, result):
        if key == 'onlineResultName':
            # like this, the user can edit the name of the
            # result before saving it to POI
            self.tempOnlinePOI.setName(result, commit=False)
            self.sendMessage('ml:notification:m:Select a category for the new POI;3')
            self.sendMessage('ml:showPOI:setupPOICategoryChooser:storePOI;setCatAndCommit')
            self.set('menu', 'menu#list#POICategoryChooser')

    def dumpToCSV(self):
        """dump the db content as a CSV file"""
        units = self.m.get('units', None)
        POIFolderPath = self.modrana.paths.getPOIFolderPath()
        self.sendMessage('ml:notification:m:POI export starting;5')
        if units and self.db:
            try:
                filenameHash = units.getTimeHashString()

                def CSVDump(path, rows):
                    """dump given list of rows to file"""
                    f = open(path, 'wb')
                    writer = csv.writer(f)
                    for row in rows:
                        writer.writerow(row)
                    f.close()

                # dump the categories
                rows = self.db.execute('select * from category').fetchall()
                filename = filenameHash + "_category_dump.csv"
                path = os.path.join(POIFolderPath, filename)
                CSVDump(path, rows)

                # dump the POI
                rows = self.db.execute('select * from poi').fetchall()
                filename = filenameHash + "_poi_dump.csv"
                path = os.path.join(POIFolderPath, filename)
                CSVDump(path, rows)

                self.sendMessage('ml:notification:m:POI exported to: %s;5' % POIFolderPath)
            except Exception:
                import sys

                e = sys.exc_info()[1]
                print("storePOI: CSV dump failed")
                print(e)
                traceback.print_exc(file=sys.stdout)
                self.sendMessage('ml:notification:m:POI export failed;5')

    def shutdown(self):
        """disconnect from the database on shutdown"""
        self.disconnectFromDb()

    def storePoint(self, point, returnToMenu=False):
        """store a given point to the POI database"""
        # TODO: automatic saving without asking
        # * skip name entry
        # * and/or skip category entry

        newPOI = self.getEmptyPOI()
        newPOI.setName(point.getName(), commit=False)
        (lat, lon) = point.getLL()
        newPOI.setLat(lat, commit=False)
        newPOI.setLon(lon, commit=False)
        newPOI.setDescription(point.getDescription())

        # temporarily store the new POI to make it
        # available during filling its name, description, etc.
        self.tempOnlinePOI = newPOI
        self.menuNameAfterStorageComplete = returnToMenu

        # start the name and description entry chain
        entry = self.m.get('textEntry', None)
        if entry:
            entry.entryBox(self, 'onlineResultName', 'POI Name', initialText=point.getName())

    def storeGLSResult(self, result):
        """store a Google Local Search result to file"""
        name = result['titleNoFormatting']
        lat = float(result['lat'])
        lon = float(result['lng'])

        newPOI = self.getEmptyPOI()
        newPOI.setName(name, commit=False)
        newPOI.setLat(lat, commit=False)
        newPOI.setLon(lon, commit=False)

        text = "%s" % (result['titleNoFormatting'])

        try: # the address can be unknown
            for addressLine in result['addressLines']:
                text += "\n%s" % addressLine
        except:
            text += "\n%s" % "no address found"

        try: # it seems, that this entry is no guarantied
            for phoneNumber in result['phoneNumbers']:
                numberType = ""
                if phoneNumber['type'] != "":
                    numberType = " (%s)" % phoneNumber['type']
                text += "\n%s%s" % (phoneNumber['number'], numberType)
        except:
            text += "\n%s" % "no phone numbers found"

        newPOI.setDescription(text, commit=False)
        self.tempOnlinePOI = newPOI

        # start the name and description entry chain
        entry = self.m.get('textEntry', None)
        if entry:
            entry.entryBox(self, 'onlineResultName', 'POI Name', name)


class POI():
    """
    !! DEPRECIATED
    A basic class representing a POI.
       DEPRECIATED, use the new version in the main class
       this is there only because it is needed for import of old POI
    !! DEPRECIATED
    """

    def __init__(self, name, category, lat, lon):
        self.name = name
        self.category = category
        self.description = ""
        self.lat = lat
        self.lon = lon

    def setDescription(self, description):
        self.description = description

    #    self.GLSResult = None # optional
