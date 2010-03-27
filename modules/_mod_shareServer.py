#!/usr/bin/python
#---------------------------------------------------------------------------
# Shares info using the pyroute share server
#---------------------------------------------------------------------------
# Copyright 2008, Oliver White
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
from base_poi import poiModule

from random import *
from urllib import *

def getModule(m,d):
  return(shareServer(m,d))

class shareServer(poiModule):
  """Shares position info with groups"""
  def __init__(self, m, d):
    poiModule.__init__(self, m, d)
 
  def update(self):
    pass
  
  def base(self):
    """Server name to use"""
    return(self.get('shareServer','http://dev.openstreetmap.org/~ojw/pos/'))
  
  def register(self):
    """Create a new username on the share server"""
    pin = randint(10000, 10000000) # random PIN
    result = self.sendRequest('newusr',{'P':pin})
    if(result[0:4] == "OK: "):
      id = int(result[4:])
      self.set('shareServerPin', pin)
      self.set('shareServerID', id)
      print "Username %d with PIN %d" % (id, pin)

  def joinGroup(self, group, group_write_pin, nickname=None):
    """Join a group, allowing you to transmit positions to it"""

    # Note: the server doesn't care about the concept of 'joining'
    # a group -- so long as you know the group's write-PIN you can
    # send to it.  This function just stores that write-PIN
    
    # Add to the list of our groups
    self.set('shareServerGroups',
      self.get('shareServerGroups','') + str(group) + ",")

    # Store the group PIN
    self.set('shareServerGroupPin_%d' % group, group_write_pin)
    
    # Optionally set a nickname for ourselves in this group
    if(nickname):
      result = self.sendRequest('nick', {
        'ID': self.get('shareServerID', 0),
        'P': self.get('shareServerPin', 0),
        'G':group,
        'WP':group_write_pin,
        'N':nickname})
      print result

  def sendPos(self, group, lat, lon):
    """Transmits your position so that the specified group can see it"""
    group_write_pin = self.get('shareServerGroupPin_%d' % group, 0)
    result = self.sendRequest('pos', {
      'ID': self.get('shareServerID', 0),
      'P': self.get('shareServerPin', 0),
      'G':group,
      'WP':group_write_pin,
      'LAT':lat,
      'LON':lon})
    print result

  def getPos(self, group, group_read_pin):
    """Get positions of all users in a group"""
    result = self.sendRequest('get', {
      'G':group,
      'RP':group_read_pin})
    users = []
    for line in result.split("\n"):
      if(line):
        (nickname,lat,lon) = line.split(",")
        users.append((nickname,lat,lon))
    return(users)
      
    

  def sendRequest(self, action, fields):
    """Used by the other functions to send requests to the server"""
    fields['A'] = action
    URL = self.base() + "?" +  urlencode(fields)
    file = self.get("shareServerTempFile", "cache/temp.txt")
    print "Sending " + URL
    urlretrieve(URL, file)
    f = open(file)
    data = f.read()
    f.close()
    return(data)
    

if __name__ == "__main__":
  d = {'shareServer':'http://dev.openstreetmap.org/~ojw/pos/',
    'shareServerTempFile':'temp.txt'}
  a = shareServer({},d)

  if(0):
    # To test uploading
    a.register();
    a.joinGroup(1,2222, "rana user")
    a.sendPos(1, 53, 12);
  else:
    # To test downloading
    print a.getPos(1, 1111)
  

