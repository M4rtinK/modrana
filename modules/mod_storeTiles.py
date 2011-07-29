from __future__ import with_statement # for python 2.5
#!/usr/bin/python
#----------------------------------------------------------------------------
# Store tiles in a single file.
# This is done to avoid the fs cluster issues.
# Initialy, sqlite will be used for storage.
#----------------------------------------------------------------------------
# Copyright 2007, Oliver White
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

from base_module import ranaModule
import sqlite3
import os
import time
import glob
import Queue
import gtk
import threading
from threading import Thread

def getModule(m,d,i):
  return(storeTiles(m,d,i))

class storeTiles(ranaModule):
  """Single-file-fs tile storage"""
  #TODO: maybe run this in separate thread ?
  
  def __init__(self, m, d, i):
    ranaModule.__init__(self, m, d, i)
    self.layers = {}
    self.threadLayers = {}
    self.currentStorageVersion = 1
    self.maxDbFileSizeGibiBytes = 3.7 # maximum database file size (to avoid the FAT32 file size limitation) in GibiBytes
    self.maxTilesInQueue = 50
    self.sqliteTileQueue = Queue.Queue(self.maxTilesInQueue)
    """if there are more tiles in the buffer than maxTilesInBuffer,
       the whole buffer will be processed at once (flushed) to avoid a potencial memmory leak
    """
    self.processPerUpdate = 1 #how many tiles will be processed per update (updates should happen every 100ms)
    self.commmitInterval=5 # how often we commit to the database (aonly happens when there is something in the queue)
    self.lastCommit=time.time()
    self.dirty = set() # a set of connections, that have uncommited data
    self.startLoadingThread()
    # locks
    """
    TODO: this lock might not be needed for python2.6+,
    as their sqlite version should be thread safe
    """
    self.lookupConnectionLock = threading.RLock()

  def firstTime(self):
    # the config folder should set the tile folder path by now
    self.tileFolder = self.get('tileFolder', 'cache/images')

    # testing:
    #self.test()

  def getLayerDbFolderPath(self, folderPrefix):
    return (self.tileFolder + "/" + folderPrefix)

  def getLookupDbPath(self, dbFolderPath):
    return "" + dbFolderPath + "/" + "lookup.sqlite" # get the path to the lookup db

  def initializeDb(self, folderPrefix, accessType):
    """there are two access types, "store" and "get"
       we basically have two connection tables, store and get ones
       the store connections are used only by the worker to store all the tiles it gets to its queue
       the get connections are used by the main thread
       when other threads query the database, they create a new connection and disconect it when done

       we still get "database locked" from time to time,
       * it may bee needed to use a mutex to control db access to fix this
       * or disconnect all database connections ?
    """
    dbFolderPath = self.getLayerDbFolderPath(folderPrefix)
    if accessType in self.layers: # do we have an entry fro this acces type ?
      if dbFolderPath in self.layers[accessType]:
        return dbFolderPath # return the lookup connection
      else:
        self.initializeLookupDb(folderPrefix,accessType) # initialize the lookup db
        return dbFolderPath
    else:
      self.layers[accessType]={} # create a new accestype entry
      self.initializeLookupDb(folderPrefix,accessType) # initialize the lookup db
      return dbFolderPath

  def initializeLookupDb(self, folderPrefix, accessType):
    """initialize the lookup database"""
    dbFolderPath = self.getLayerDbFolderPath(folderPrefix) # get the layer folder path

    if not os.path.exists(dbFolderPath): # does the folder exist ?
      os.makedirs(dbFolderPath) # create the folder

    lookupDbPath = self.getLookupDbPath(dbFolderPath) # get the path

    if dbFolderPath not in self.layers.keys():
      print "sqlite tiles: initializing db for layer: %s" % folderPrefix
      if os.path.exists(lookupDbPath): #does the lookup db exist ?
        connection = sqlite3.connect(lookupDbPath) # connect to the lookup db
      else: #create new lookup db
        connection = sqlite3.connect(lookupDbPath)
        cursor = connection.cursor()
        print "sqlite tiles: creating lookup table"
        cursor.execute("create table tiles (z integer, x integer, y integer, store_filename string, extension varchar(10), unix_epoch_timestamp integer, primary key (z, x, y, extension))")
        cursor.execute("create table version (v integer)")
        cursor.execute("insert into version values (?)", (self.currentStorageVersion,))
        connection.commit()
      self.layers[accessType][dbFolderPath] = {'lookup':connection, 'stores':{}}


  def storeTile(self, tile, folderPrefix, z, x, y, extension):
    if self.get('storeDownloadedTiles', True):
      accessType = "store"
      dbFolderPath = self.initializeDb(folderPrefix,accessType)
      if dbFolderPath!=None:
          lookupConn = self.layers[accessType][dbFolderPath]['lookup'] # connect to the lookup db
      stores = self.layers[accessType][dbFolderPath]['stores'] # get a list of cached store connections

      lookupCursor = lookupConn.cursor()
      with self.lookupConnectionLock:
        """ just to make sure the access is sequential
        (due to sqlite in python 2.5 probably not liking concurrent access,
        resulting in te database becomming unavailable)"""
        result = lookupCursor.execute("select store_filename, unix_epoch_timestamp from tiles where z=? and x=? and y=? and extension=?", (z, x, y, extension))
        if not result.fetchone():
          # store the tile as its not already in the database

          # get a store path
          size = len(tile)
          pathToStore = self.getAnAvailableStorePath(folderPrefix, size)

          # connect to the store
          storeConn = self.connectToStore(stores, pathToStore, dbFolderPath, accessType)

          # store the tile
          integerTimestamp = int(time.time())
          try:
            ## 1. write in the lookup db (its easier to remove pointers to nonexisting stuff than to remove orphaned store items)
            storeFilename = os.path.basename(pathToStore)
            lookupQuery="insert into tiles (z, x, y, store_filename, extension, unix_epoch_timestamp) values (?, ?, ?, ?, ?, ?)"
            lookupCursor = lookupConn.cursor()
            lookupCursor.execute(lookupQuery,[z,x,y,storeFilename, extension, integerTimestamp])

            ## 2. write in the store
            storeQuery="insert into tiles (z, x, y, tile, extension, unix_epoch_timestamp) values (?, ?, ?, ?, ?, ?)"
            storeCursor = storeConn.cursor()
            storeCursor.execute(storeQuery,[z,x,y,sqlite3.Binary(tile), extension, integerTimestamp])
            self.commitConnections([storeConn,lookupConn])
          except Exception, e:
            print "tile already present"
            print e
            pass #tile is already present, skip insert

  def commitConnections(self,connections):
    """store connections and commit them once in a while"""
    for c in connections:
      self.dirty.add(c)


  def commitAll(self):
    """commit all uncommited"""
    with self.lookupConnectionLock:
      """ just to make sure the access is sequential
      (due to sqlite in python 2.5 probably not liking concurrent access,
      resulting in te database becomming unavailable)"""
      while self.dirty:
        conn = self.dirty.pop()
        conn.commit()
      print "storeTiles: sqlite committ OK"



  def connectToStore(self, stores, pathToStore, dbFolderPath, accessType):
    """connect to a store
       * use an existing connection or create a new one"""
    if pathToStore in stores.keys():
      return stores[pathToStore] # there is already a connection to the store, return it
    else: # create a new connection
      with self.lookupConnectionLock:
        """ just to make sure the access is sequential
        (due to sqlite in python 2.5 probably not liking concurrent access,
        resulting in te database becomming unavailable)"""
        storeConn = sqlite3.connect(pathToStore) #TODO: add some error handling
        self.layers[accessType][dbFolderPath]['stores'][pathToStore] = storeConn # cache the connection
        return storeConn

  def getAnAvailableStorePath(self, folderPrefix, size):
    """return a path to a store that can be used to store a tile specified by size"""
    layerDbFolderPath = self.getLayerDbFolderPath(folderPrefix)
    storeList = self.listStores(layerDbFolderPath)
    if storeList: # there are already some stores
      availableStores = []
      for storePath in storeList: # iterate over the available stores
        cleanPath =  storePath.rstrip('-journal') # dont add sqlite journal files
        if self.willItFitIn(cleanPath, size):# add all stores that can be used to store the current object
          availableStores.append(cleanPath)

      if availableStores: # did we find some stores ?
        availableStorePath = availableStores.pop() # use one of the stores
      else:
        availableStorePath = self.addStore(layerDbFolderPath) # all stores full, add a new one

    else: #there are no stores, add one
      availableStorePath = self.addStore(layerDbFolderPath)

    return availableStorePath


  def listStores(self, folder):
    """search for available store database files"""
    return glob.glob("" + folder + "/" + "store.sqlite.*")


  def willItFitIn(self, path, sizeBytes):
    """ True  = probably fits in the database
        False = would not fit in
        NOTE: there is some database overhead, so this is not 100% reliable
              always set the limit with a slight margin"""

    gibiByte = 1073741824
    maximumSizeBytes = self.maxDbFileSizeGibiBytes*gibiByte
    pathSizeBytes = os.path.getsize(path)
    if (pathSizeBytes+sizeBytes)<=maximumSizeBytes:
      return True # the database will (probably) still smaler than the limit
    else:
      return False # the database will be larger

  def addStore(self, folder):
    """add a new store(find an ascending numbered name and create the db file with the corresponding tables)"""
    list = self.listStores(folder)
    if list:
      numericList = map(lambda x: int(x.split('store.sqlite.')[1]),list)
      highestNumber = sorted(numericList)[-1]
      newHighestNumber = highestNumber + 1
    else:
      newHighestNumber = 0

    storeName = "store.sqlite.%d" % newHighestNumber
    newStorePath = self.getStorePath(folder, storeName)
    return self.createNewStore(newStorePath)

  def createNewStore(self, path):
    """create a new store table and file"""
    print "sqlite tiles: creating a new storage database in %s" % path
    os.path.exists(path)
    connection = sqlite3.connect(path)
    cursor = connection.cursor()
    cursor.execute("create table tiles (z integer, x integer, y integer, tile blob, extension varchar(10), unix_epoch_timestamp integer, primary key (z, x, y, extension))")
    cursor.execute("create table version (v integer)")
    cursor.execute("insert into version values (?)", (self.currentStorageVersion,))
    connection.commit()
    return path

  def getStorePath(self, folder, storeName):
    """get a standardized store path from folder path and filename"""
    return folder + "/" + storeName

  def getTile(self, folderPrefix, z, x, y, extension):
    """get a tile"""
    storageType = self.get('tileStorageType', 'files')
    if storageType == 'sqlite':
      accessType = "get"
      dbFolderPath = self.initializeDb(folderPrefix, accessType)
      if dbFolderPath!=None:
        lookupConn = self.layers[accessType][dbFolderPath]['lookup'] # connect to the lookup db
        result = self.getTileFromDb(lookupConn, dbFolderPath, z, x, y, extension)
        if result: # is the result valid ?
          resultContent = result.fetchone() # get the result content
        else:
          resultContent = None # the result is invalid
        if resultContent:
          # convert the buffer to pixbuf
          try:
            pl = gtk.gdk.PixbufLoader()
            pl.write(resultContent[0])
            pl.close()
            pixbuf = pl.get_pixbuf()
            return pixbuf # return pixbuf containing the tile image
          except Exception, e:
            print "loading the image buffer from sqlite to pixbuf failed:%s" % e
        else:
          return None # the tile is not stored
    else: # the only other storage method is currently clasical files storage
      mapTiles = self.m.get('mapTiles', None)
      if mapTiles:
        tileFolderPath = mapTiles._getTileFolderPath()
        layerFolderAndTileFilename = mapTiles.getImagePath(x,y,z,folderPrefix, extension)
        tilePath = os.path.join(tileFolderPath, layerFolderAndTileFilename)
        if os.path.exists(tilePath):
          # load the file to pixbuf and return it
          return mapTiles.filePath2Pixbuf(tilePath)
        else:
          return None # this tile is not locally stored

  def getTileFromDb(self, lookupConn, dbFolderPath, z, x, y, extension):
    """get a tile from the database"""
    accessType = "get"
    #look in the lookup db
    with self.lookupConnectionLock:
      """ just to make sure the access is sequential
      (due to sqlite in python 2.5 probably not liking concurrent access,
      resulting in te database becomming unavailable)"""
      lookupCursor = lookupConn.cursor()
      lookupResult = lookupCursor.execute("select store_filename, unix_epoch_timestamp from tiles where z=? and x=? and y=? and extension=?", (z, x, y, extension)).fetchone()
      if lookupResult: # the tile was found in the lookup db
        # now search in the store
        storeFilename = lookupResult[0]
        pathToStore = self.getStorePath(dbFolderPath, storeFilename)
        stores = self.layers[accessType][dbFolderPath]['stores']
        connectionToStore = self.connectToStore(stores, pathToStore, dbFolderPath, accessType)
        storeCursor = connectionToStore.cursor()
        result = storeCursor.execute("select tile, unix_epoch_timestamp from tiles where z=? and x=? and y=? and extension=?", (z, x, y, extension))
        return result
      else: # the tile was not found in the lookup table
        return None

  def tileExists(self, filePath, folderPrefix, z, x, y, extension, fromThread=False):
    """test if a tile exists
       if fromThread=False, a new connection is created and disconnected again"""
    storageType = self.get('tileStorageType', 'files')
    if storageType == 'sqlite': # we are storing to the database
      dbFolderPath = self.getLayerDbFolderPath(folderPrefix)
      if dbFolderPath!=None: # is the database accessible ?
        with self.lookupConnectionLock:
          """ just to make sure the access is sequential
          (due to sqlite in python 2.5 probably not liking concurrent access,
          resulting in te database becomming unavailable)"""
          if fromThread: # is this called from a thread ?
            # due to sqlite quirsk, connections can't be shared between threads
            lookupDbPath = self.getLookupDbPath(dbFolderPath)
            lookupConn = sqlite3.connect(lookupDbPath)
          else:
            lookupConn = self.layers[dbFolderPath]['lookup'] # connect to the lookup db
          query = "select store_filename, unix_epoch_timestamp from tiles where z=? and x=? and y=? and extension=?"
          lookupResult = lookupConn.execute(query,(z, x, y, extension)).fetchone()
          if fromThread: # tidy up, just to be sure
            lookupConn.close()
          if lookupResult:
            return True # the tile is in the db
          else:
              return False # the tile is not in the db
      else:
        return None # we cant decide if a tile is ind the db or not
    else: # we are storing to the filesystem
      return os.path.exists(filePath)

  def startLoadingThread(self):
    """start the sqlite loading thread"""
    t = Thread(target=self.worker, name='sqlite tile storage thread')
    """we need that the worker tidies up,
       (commits all "dirty" conections)
       so it should be not daemonic
       -> but we also cant affort that modrana wont
       terminate completely
       """
    t.setDaemon(True)
    t.start()


  def worker(self):
    """this is run by a thread that stores sqlite tiles to a db"""
    while True:
        try:
          item = self.sqliteTileQueue.get(block=True)
        except Exception, e:
          """this usually occurs during interpreter shutdown
             -> we simulate a shutdown order and try to exit cleanly
             """
          print "storage thread - probable shutdown"
          print "exception: %s" % e
          item = 'shutdown'

        if item=='shutdown': # we put this to the queue to announce shutdown
          print "\nshutdown imminent, commiting all uncommited tiles"
          self.commitAll()
          print "\nall tiles commited, breaking, goodbye :)"
          break
        """
        the thread should not die due to an exception
        or the queue fills up without anybody removing and processing the tiles
        -> this would mean that all threads that need to store tiles
           would wait forewer for the queue to empty
        """
        try:
          (tile, folderPrefix, z, x, y, extension, filename) = item # unpack the tupple
          self.storeTile(tile, folderPrefix, z, x, y, extension) # store the tile
          self.sqliteTileQueue.task_done()
        except Exception, e:
          print "sqlite storage worker : exception during tile storage:\n%s" % e

        dt = time.time() - self.lastCommit # check when the last commit was
        if dt>self.commmitInterval:
          try:
            self.commitAll() # commit all "dirty" connections
            self.lastCommit = time.time() # update the last commit timestamp
          except Exception, e:
            print "sqlite storage worker : exception during mass db commit:\n%s" % e


  def automaticStoreTile(self, tile, folderPrefix, z, x, y, extension, filename, fromThread = False):
    """store a tile to a file or db, depending on the current setting"""

    storageType = self.get('tileStorageType', 'files')
    if storageType == 'sqlite': # we are storing to the database
      # put the tile to the storage queue, so that then worker can store it
      self.sqliteTileQueue.put((tile, folderPrefix, z, x, y, extension, filename), block=True, timeout=20)
    else: # we are storing to the filesystem
      # get the folder path
      (folderPath, tail) = os.path.split(filename)
      if not os.path.exists(folderPath): # does it exist ?
        try:
          os.makedirs(folderPath) # create the folder
        except:
          print "mapTiles: cant create folder %s for %s" % (folderPath,filename)

      f = open(filename, 'w') # write the tile to a file
      f.write(tile)
      f.close()

  def shutdown(self):
#    accessType = "get"
#    folderPrefix = 'OpenStreetMap I'
#    dbFolderPath = self.initializeDb(folderPrefix, accessType)
##    lookupConn = self.layers[accessType][dbFolderPath]['lookup']
#    start = time.clock()
#
#    temp = [(13, 4466, 2815, 'png'), (13, 4466, 2816, 'png'), (13, 4467, 2815, 'png'), (13, 4467, 2816, 'png'), (13, 4468, 2815, 'png'), (13, 4468, 2816, 'png'), (13, 4469, 2815, 'png'), (13, 4469, 2816, 'png'), (13, 4467, 2814, 'png'), (13, 4468, 2814, 'png'), (13, 4469, 2814, 'png'), (13, 4470, 2814, 'png'), (13, 4470, 2815, 'png'), (13, 4470, 2816, 'png'), (13, 4471, 2814, 'png'), (13, 4471, 2815, 'png'), (13, 4471, 2816, 'png'), (13, 4472, 2814, 'png'), (13, 4472, 2815, 'png'), (13, 4472, 2816, 'png'), (13, 4473, 2814, 'png'), (13, 4473, 2815, 'png'), (13, 4473, 2816, 'png'), (13, 4474, 2814, 'png'), (13, 4474, 2815, 'png'), (13, 4474, 2816, 'png'), (13, 4475, 2814, 'png'), (13, 4475, 2815, 'png'), (13, 4475, 2816, 'png'), (13, 4476, 2814, 'png'), (13, 4476, 2815, 'png'), (13, 4476, 2816, 'png'), (13, 4477, 2814, 'png'), (13, 4477, 2815, 'png'), (13, 4477, 2816, 'png'), (13, 4478, 2814, 'png'), (13, 4478, 2815, 'png'), (13, 4478, 2816, 'png'), (13, 4479, 2814, 'png'), (13, 4479, 2815, 'png'), (13, 4479, 2816, 'png'), (13, 4480, 2814, 'png'), (13, 4480, 2815, 'png'), (13, 4480, 2816, 'png'), (13, 4481, 2814, 'png'), (13, 4481, 2815, 'png'), (13, 4481, 2816, 'png'), (13, 4482, 2814, 'png'), (13, 4482, 2815, 'png'), (13, 4483, 2814, 'png'), (13, 4483, 2815, 'png'), (13, 4484, 2814, 'png'), (13, 4484, 2815, 'png'), (13, 4485, 2814, 'png'), (13, 4485, 2815, 'png'), (13, 4486, 2814, 'png'), (13, 4486, 2815, 'png'), (13, 4485, 2813, 'png'), (13, 4486, 2813, 'png'), (13, 4487, 2813, 'png'), (13, 4487, 2814, 'png'), (13, 4487, 2815, 'png'), (13, 4488, 2813, 'png'), (13, 4488, 2814, 'png'), (13, 4488, 2815, 'png'), (13, 4481, 2813, 'png'), (13, 4482, 2813, 'png'), (13, 4483, 2813, 'png'), (13, 4484, 2813, 'png'), (13, 4480, 2813, 'png'), (13, 4477, 2812, 'png'), (13, 4477, 2813, 'png'), (13, 4478, 2812, 'png'), (13, 4478, 2813, 'png'), (13, 4479, 2812, 'png'), (13, 4479, 2813, 'png'), (13, 4480, 2812, 'png'), (13, 4475, 2811, 'png'), (13, 4475, 2812, 'png'), (13, 4475, 2813, 'png'), (13, 4476, 2811, 'png'), (13, 4476, 2812, 'png'), (13, 4476, 2813, 'png'), (13, 4477, 2811, 'png'), (13, 4478, 2811, 'png'), (13, 4474, 2810, 'png'), (13, 4474, 2811, 'png'), (13, 4474, 2812, 'png'), (13, 4475, 2810, 'png'), (13, 4476, 2810, 'png'), (13, 4477, 2810, 'png'), (13, 4473, 2810, 'png'), (13, 4473, 2811, 'png'), (13, 4473, 2812, 'png')]
#
#    print len(temp), "tiles"
#    for tile in temp:
#      (z, x, y, extension) = tile
#
#      lookupDbPath = self.getLookupDbPath(dbFolderPath)
#      lookupConn = sqlite3.connect(lookupDbPath)
#      lookupCursor = lookupConn.cursor()
#      lookupResult = lookupCursor.execute("select store_filename, unix_epoch_timestamp from tiles where z=? and x=? and y=? and extension=?", (z, x, y, extension)).fetchone()
#      lookupConn.close()
#    print "no connection reuse %f ms" % (1000 * (time.clock() - start))
#
#    start = time.clock()
#    lookupDbPath = self.getLookupDbPath(dbFolderPath)
#    lookupConn = sqlite3.connect(lookupDbPath)
#    lookupCursor = lookupConn.cursor()
#    for tile in temp:
#      (z, x, y, extension) = tile
#      lookupResult = lookupCursor.execute("select store_filename, unix_epoch_timestamp from tiles where z=? and x=? and y=? and extension=?", (z, x, y, extension)).fetchone()
#      print lookupResult
#    lookupCursor.close()
#    lookupConn.close()
#    print "connection reuse %f ms" % (1000 * (time.clock() - start))


    self.sqliteTileQueue.put('shutdown',True) # try to commit possible uncommited tiles

if(__name__ == "__main__"):
  a = example({}, {})
  a.update()
  a.update()
  a.update()
