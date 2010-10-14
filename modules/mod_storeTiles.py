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
from threading import Thread

def getModule(m,d):
  return(storeTiles(m,d))

class storeTiles(ranaModule):
  """Single-file-fs tile storage"""
  #TODO: maybe run this in separate thread ?
  
  def __init__(self, m, d):
    ranaModule.__init__(self, m, d)
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
    accessType = "store"
    dbFolderPath = self.initializeDb(folderPrefix,accessType)
    if dbFolderPath!=None:
        lookupConn = self.layers[accessType][dbFolderPath]['lookup'] # connect to the lookup db
    stores = self.layers[accessType][dbFolderPath]['stores'] # get a list of cached store connections

    lookupCursor = lookupConn.cursor()
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
    """commit are uncommited"""
    while self.dirty:
      conn = self.dirty.pop()
      conn.commit()
    print "committ OK"



  def connectToStore(self, stores, pathToStore, dbFolderPath, accessType):
    """connect to a store
       * use an existing connection or create a new one"""
    if pathToStore in stores.keys():
      return stores[pathToStore] # there is already a connection to the store, return it
    else: # create a new connection
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
        return resultContent[0] # return the tile image data buffer
      else:
        return None # the tile is not stored

  def getTileFromDb(self, lookupConn, dbFolderPath, z, x, y, extension):
    """get a tile from the database"""
    accessType = "get"
    #look in the lookup db
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

  def worker(self):
    """this is run by a thread that stores sqlite tiles to a db"""
    while True:
        item = self.sqliteTileQueue.get(block=True)
        if item=='shutdown': # we put this to the queue to announce shutdown
          print "\nshutdown imminent, commiting all tiles"
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
          (tile, folderPrefix, z, x, y, extension, filename, folder) = item # unpack the tupple
          self.storeTile(tile, folderPrefix, z, x, y, extension) # store the tile
          self.sqliteTileQueue.task_done()
        except Exception, e:
          print "sqlite storage worker -> exception during tile storage:\n%s" % e

        dt = time.time() - self.lastCommit # check when the last commit was
        if dt>self.commmitInterval:
          try:
            self.commitAll() # commit all "dirty" connections
            self.lastCommit = time.time() # update the last commit timestamp
          except Exception, e:
            print "sqlite storage worker -> exception during mass db commit:\n%s" % e



  def startLoadingThread(self):
    """start the sqlite loading thread"""
    t = Thread(target=self.worker)
    """we need that the worker tidies up,
       (commits all "dirty" conections)
       so it is not daemonic"""
#    t.daemon = True
    t.start()


  def automaticStoreTile(self, tile, folderPrefix, z, x, y, extension, filename, folder, fromThread = False):
    """store a tile to a file or db, depending on the current setting"""

    storageType = self.get('tileStorageType', 'files')
    if storageType == 'sqlite': # we are storing to the database
      # put the tile to the storage queue, so that then worker can store it
      self.sqliteTileQueue.put((tile, folderPrefix, z, x, y, extension, filename, folder), block=True, timeout=20)
    else: # we are storing to the filesystem
      if not os.path.exists(folder): # does it exist ?
        try:
          os.makedirs(folder) # create the folder
        except:
          print "mapTiles: cant crate folder %s for %s" % (folder,filename)
      f = open(filename, 'w') # write the tile to file
      f.write(tile)
      f.close()

  def shutdown(self):
    self.sqliteTileQueue.put('shutdown',True) # try to commit possible uncommited tiles

#  def update(self):
#    if not self.sqliteTileQueue.empty():
#      print "queue: %d" % self.sqliteTileQueue.qsize()

if(__name__ == "__main__"):
  a = example({}, {})
  a.update()
  a.update()
  a.update()
