#!/usr/bin/python
import urllib

path = '/tmp/'
filename1 = 'modRana_test_i_connectivity_google.jpg'
filename2 = 'modRana_test_i_connectivity_google.jpg'
google = 'http://www.google.com/intl/en_ALL/images/logo.gif'
osm = 'http://b.tile.openstreetmap.org/17/71964/44884.png'
print "trying to download Google logo (%s) to /tmp/" % google
print "(%s)" % google
try:
  urllib.urlretrieve(google, path+filename1)
  print "Google logo: download OK"
except Exception, e:
  print "error while downloading Google logo: %s" % e


print "trying to download an OSM tile (%s) to /tmp/" % osm
print "(%s)" % osm
try:
  urllib.urlretrieve(osm, path+filename2)
  print "OSM tile: download OK"
except Exception, e:
  print "error while downloading an OSM tile: %s" % e