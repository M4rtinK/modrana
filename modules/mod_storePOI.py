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
import csv
from core.point import POI
from core.poi_db import POIDatabase

def getModule(*args, **kwargs):
    return StorePOI(*args, **kwargs)


class StorePOI(RanaModule):
    """Store POI data."""

    def __init__(self, *args, **kwargs):
        RanaModule.__init__(self, *args, **kwargs)
        self.tempOnlinePOI = None # temporary slot for an uncommitted POI from online search
        # to which menu to return after the POI is stored
        # NOTE: False => unset, None => map screen
        self.menuNameAfterStorageComplete = False
        # connect to the POI database
        self._db = self.connect_to_database()

    @property
    def db(self):
        return self._db

    def firstTime(self):
        self._check_import() # check if there ary any old POI to import

    def connect_to_database(self):
        """Connect to the POI database"""
        db_path = self.modrana.paths.poi_database_path
        return POIDatabase(db_path=db_path)

    def getEmptyPOI(self):
        """Get a POI with all variables set to None"""
        poiObject = POI(None, None, None, None, None, None)
        return poiObject

    def _check_import(self):
        """Check if there are any POI in the old format
           and try to import them to the db (into the "other" category)
           then rename the old poi file to prevent multiple imports"""

        oldPOIPath = "data/poi/poi.txt"
        if os.path.exists(oldPOIPath):
            try:
                renamedOldPOIPath = "data/poi/imported_old_poi.txt"
                self.log.info("importing old POI from: %s", oldPOIPath)
                points = self._load_old_poi(oldPOIPath)
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

    def _load_old_poi(self, path):
        """Load POI from file - depreciated, used sqlite for POI storage"""
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
                poi_db_index = int(args)
                if self._db:
                    self._db.delete_poi(poi_db_index)  # remove the poi from database
                # notify the showPOI module, that it might need to rebuild its menus
                self.sendMessage('showPOI:listMenusDirty')
        elif messageType == 'ms' and message == 'setCatAndCommit':
            # set category and as this is the last needed input,
            # commit the new POI to the database
            cat_db_index = int(args)
            # set the category to the one the user just selected
            self.tempOnlinePOI.db_category_index = int(args)
            # commit the new online result based POI to db
            self.tempOnlinePOI.commit()
            # signal that the showPOI menus may need to be regenerated
            self.sendMessage('showPOI:listMenusDirty')
            if not self._db:
                self.log.error("can't set category: POI database not available")
                return
            category_info = self._db.get_category_from_index(cat_db_index)
            category_name = category_info[1]
            poi_name = self.tempOnlinePOI.name
            # NOTE: False means the the variable is unset, as None means the map screen
            if self.menuNameAfterStorageComplete == False:
                self.set('menu', 'search#searchResultsItem')
            else:
                self.set('menu', self.menuNameAfterStorageComplete)

            self.sendMessage('ml:notification:m:%s has been saved to %s;5' % (poi_name, category_name))

        elif message == "reconnectToDb":
            # this means, that we need to reconnect the database
            # * this is used for example when the user changed
            #   the default POI database path
            self._db.disconnect_from_database()
            self.connect_to_database()

        elif message == "dumpToCSV":
            # dump db to CSV file
            self.set('menu', None)
            self._dump_to_CSV()

    def _dump_to_CSV(self):
        """Dump the database content as a CSV file"""
        units = self.m.get('units', None)
        POIFolderPath = self.modrana.paths.poi_folder_path
        self.sendMessage('ml:notification:m:POI export starting;5')
        if units and self.db:
            try:
                filenameHash = units.getTimeHashString()

                def CSVDump(csv_path, csv_rows):
                    """dump given list of rows to file"""
                    f = open(csv_path, 'wb')
                    writer = csv.writer(f)
                    for row in csv_rows:
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
        """Disconnect from the database on shutdown"""
        self._db.disconnect_from_database()
        self._db = None

    def storePoint(self, point, returnToMenu=False):
        """Store a given point to the POI database"""
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
        """Store a local search result to the database"""

        (lat, lon) = result.getLL()
        newPOI = POI(name=result.name, description=result.description,
                     lat=lat, lon=lon, db_cat_id=None)

        self.tempOnlinePOI = newPOI

        # start the name and description entry chain
        entry = self.m.get('textEntry', None)
        if entry:
            entry.entryBox(self, 'onlineResultName', 'POI Name', result.name)
