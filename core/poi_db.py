"""A modRana POI database class"""

import os
import sys
import sqlite3
from core.point import POI
from core.backports.six import u

PYTHON3 = sys.version_info[0] > 2

import logging
log = logging.getLogger("core.poi_db")


class DatabaseConnectionFailed(Exception):
    """Raised if connection to the underlying database could not be established"""
    pass

class DatabaseNotConnected(Exception):
    """Raised when an attempt is made to use a database that is not properly connected

    NOTE: We generally only raise this exception when attempts are made to write an
          unconnected database, as that might otherwise lead to data loss.
          On the other hand read attempts for an unconnected database just return results
          like if the database was empty.
    """
    pass

class POIDatabase(object):
    def __init__(self, db_path):
        """
        :param str db_path: path to the POI database file
        If no POI database exists on the given path a new empty
        database file will be created and initialized.
        """
        self._db = None
        if os.path.exists(db_path): # connect to existing db
            log.info("POI database path:")
            log.info(db_path)
            try:
                self._db = sqlite3.connect(database=db_path)
                log.info("connection to POI db established")
            except Exception:
                log.exception("connecting to POI database failed")
                raise DatabaseConnectionFailed

        else: # create new db
            try:
                self._db = self.create_empty_db(db_path)
            except Exception:
                log.exception("POI database creation failed")
                raise DatabaseConnectionFailed

    @property
    def connected(self):
        """Report if we are connected to the underlying database"""
        return bool(self._db)

    def create_empty_db(self, db_path):
        """Create a new database, including tables and initial data

        :returns: the SQLite connection object
        """
        log.debug("creating new database file in:\n%s", db_path)
        conn = sqlite3.connect(db_path)

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
        log.debug("new database file has been created")
        return conn

    def disconnect_from_database(self):
        """Close the connection to the underlying SQLite database"""
        log.info("disconnecting from POI db")
        if self.connected:
            self._db.close()
            self._db = None

    def _get_poi_db_order(self, poi):
        """Get values from a POI object in the database order

        :param poi: POI object to "serialize"
        :returns: POI object values tuple for storage in database order
        :rtype: tuple
        """
        if PYTHON3:
            name = poi.name
            description = poi.description
        else:
            name = poi.name.decode("utf-8")
            description = poi.description.decode("utf-8")

        return (
            poi.db_index,
            poi.lat,
            poi.lon,
            name,
            description,
            poi.db_category_index
        )

    def store_poi(self, poi):
        """Store a POI object to the database

        :param poi: POI object instance
        :raises: DatabaseNotConnected if database is not connected
        """
        if self.connected:
            values = self._get_poi_db_order(poi)
            query = "replace into poi values(?,?,?,?,?,?)"
            cursor = self._db.cursor()
            cursor.execute(query, values)
            db_id = cursor.lastrowid
            self._db.commit()
            return db_id
        else:
            raise DatabaseNotConnected

    def delete_poi(self, poi_db_index):
        """Delete a poi with given ID from the database

        :param int poi_db_index: database index of the POI to delete
        :raises: DatabaseNotConnected if database is not connected
        """
        if self.connected:
            self._db.execute('delete from poi where poi_id=?', [poi_db_index])
            self._db.commit()
        else:
            raise DatabaseNotConnected

    def list_categories(self):
        """Return a list of all available categories

        :returns: list of all available categories
        :rtype: list of tuples
        """
        if self.connected:
            return self._db.execute('select label,desc,cat_id from category').fetchall()
        else:
            return []

    def list_used_categories(self):
        """Return a list of categories that have at least one POI

        :returns: list of categories that have at least one POI
        :rtype: list of POI objects
        """
        if self.connected:
            # find which POI categories are actually used
            # TODO: investigate how this scales for many points
            usedCatIds = self._db.execute('select distinct cat_id from poi').fetchall()
            usedCategories = []
            for catId in usedCatIds:
                nameDescription = self._db.execute('select label,desc,cat_id from category where cat_id=?',
                                                  catId).fetchone()
                if nameDescription:
                    usedCategories.append(nameDescription)
            return usedCategories #this should be a list of used category ids
        else:
            return []

    def get_category_from_index(self, category_db_index):
        """Returns category data corresponding to the given category db index

        :param int category_db_index: category database index
        :returns: a (cat_id,label, desc, enabled) tuple or None if nothing is found
        :rtype: tuple or None
        """
        if self.connected:
            result = self._db.execute('select cat_id,label,desc,enabled from category where cat_id=?', [category_db_index]).fetchone()
            return result
        else:
            return []

    def get_category_from_name(self, category_name):
        """Return category data corresponding to the given category name

        :param str category_name: category name
        :returns: a (cat_id,label, desc, enabled) tuple or None if nothing is found
        :rtype: tuple or None
        """
        if self.connected:
            result = self._db.execute('select cat_id,label,desc,enabled from category where label=?', [category_name]).fetchone()
            return result
        else:
            return None

    def get_all_poi_from_category(self, category_db_index):
        """Return a list of all POI for the given category database index

        :param int category_db_index: category database index
        :returns: a list of POI from the given category or None if category is unknown or empty
        :rtype: list of POI objects or None
        """
        if self.connected:
            result = self._db.execute('select label,desc,lat,lon,poi_id from poi where cat_id=?', [category_db_index]).fetchall()
            return result
        else:
            return None

    def get_poi(self, poi_db_index):
        """Return a complete POI row from db fow a given POI id

        :param int poi_db_index: database index of the POI to retrieve from the database
        :returns: POI object or None
        :rtype: POI or None
        """
        if self.connected:
            result = self._db.execute('select poi_id, lat, lon, label, desc, cat_id from poi where poi_id=?',
                                     [poi_db_index]).fetchone()
            if result:
                (poi_id, lat, lon, name, desc, cat_id) = result
                # make it more usable
                poiObject = POI(name, desc, lat, lon, cat_id, poi_id)
                return poiObject
            else:
                return None
        else:
            return None