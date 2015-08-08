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
from modules.base_module import RanaModule
import os
import sqlite3
import csv
from core.backports.six import u
from core.point import POI

def getModule(*args, **kwargs):
    return StorePOI(*args, **kwargs)


class StorePOI(RanaModule):
    """Store POI data."""

    def __init__(self, *args, **kwargs):
        RanaModule.__init__(self, *args, **kwargs)
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
            self.log.info("POI database path:")
            self.log.info(DBPath)
            try:
                self.db = sqlite3.connect(DBPath)
                self.log.info("connection to POI db established")
            except Exception:
                self.log.exception("connecting to POI database failed")

        else: # create new db
            try:
                self.db = self.createDatabase(DBPath)
            except Exception:
                self.log.exception("POI database creation failed")

    def disconnectFromDb(self):
        self.log.info("disconnecting from POI db")
        if self.db:
            self.db.close()

    def createDatabase(self, path):
        """create a new database, including tables and initial data
        return the connection object"""
        self.log.debug("creating new database file in:")
        self.log.debug(path)
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
        self.log.debug("new database file has been created")
        return conn

    def storePOI(self, poi_instance):
        """store a POI object to the database"""
        if self.db:
            values = poi_instance.get_db_order()
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
        """Return a complete POI row from db fow a given POI id"""
        if self.db:
            result = self.db.execute('select poi_id, lat, lon, label, desc, cat_id from poi where poi_id=?',
                                     [POIId]).fetchone()
            if result:
                (poi_id, lat, lon, name, desc, cat_id) = result
                # make it more usable
                poiObject = POI(name, desc, lat, lon, cat_id, poi_id)
                return poiObject
            else:
                return None
        else:
            return None

    def getEmptyPOI(self):
        """Get a POI with all variables set to None"""
        poiObject = POI(None, None, None, None, None, None)
        return poiObject

    def checkImport(self):
        """Check if there are any POI in the old format
           and try to import them to the db (into the "other" category)
           then rename the old poi file to prevent multiple imports"""

        oldPOIPath = "data/poi/poi.txt"
        if os.path.exists(oldPOIPath):
            try:
                renamedOldPOIPath = "data/poi/imported_old_poi.txt"
                self.log.info("importing old POI from: %s", oldPOIPath)
                points = self.loadOld(oldPOIPath)
                if points:
                    for point in points:
                        # create a new POI object
                        name = point.name
                        description = point.description.replace('|', '\n')
                        lat = point.lat
                        lon = point.lon
                        catId = 11
                        newPOI = POI(name, description, lat, lon, catId)
                        newPOI.commit()
                    self.log.info("imported %d old POI", len(points))
                    os.rename(oldPOIPath, renamedOldPOIPath)
                    self.log.info("old POI file moved to: %s", renamedOldPOIPath)
                    self.sendMessage('ml:notification:m:%d old POI imported to category "Other";10' % len(points))
            except Exception:
                self.log.exception("import of old POI failed")

    def loadOld(self, path):
        """load POI from file - depreciated, used sqlite for POI storage"""
        try:
            f = open(path, 'r')
            import pickle

            points = pickle.load(f)
            f.close()
            return points
        except Exception:
            self.log.exception("loading POI from file failed")
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
            # commit the new POI to the database
            catId = int(args)
            # set the category to the one the user just selected
            self.tempOnlinePOI.db_category_index = int(args)
            # commit the new online result based POI to db
            self.tempOnlinePOI.commit()
            # signal that the showPOI menus may need to be regenerated
            self.sendMessage('showPOI:listMenusDirty')
            catInfo = self.getCategoryForId(catId)
            catName = catInfo[1]
            POIName = self.tempOnlinePOI.name
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
            self.tempOnlinePOI.name = result
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
                self.log.exception("CSV dump failed")
                self.sendMessage('ml:notification:m:POI export failed;5')

    def shutdown(self):
        """disconnect from the database on shutdown"""
        self.disconnectFromDb()

    def storePoint(self, point, returnToMenu=False):
        """store a given point to the POI database"""
        # TODO: automatic saving without asking
        # * skip name entry
        # * and/or skip category entry
        (lat, lon) = point.getLL()
        newPOI = POI(name=point.name, description=point.description,
                     lat=lat, lon=lon, db_cat_id=None)


        # temporarily store the new POI to make it
        # available during filling its name, description, etc.
        self.tempOnlinePOI = newPOI
        self.menuNameAfterStorageComplete = returnToMenu

        # start the name and description entry chain
        entry = self.m.get('textEntry', None)
        if entry:
            entry.entryBox(self, 'onlineResultName', 'POI Name', initialText=point.name)

    def storeLocalSearchResult(self, result):
        """store a local search result to the database"""

        (lat, lon) = result.getLL()
        newPOI = POI(name=result.name, description=result.description,
                     lat=lat, lon=lon, db_cat_id=None)

        self.tempOnlinePOI = newPOI

        # start the name and description entry chain
        entry = self.m.get('textEntry', None)
        if entry:
            entry.entryBox(self, 'onlineResultName', 'POI Name', result.name)


