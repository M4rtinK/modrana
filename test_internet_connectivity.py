#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib
import urllib2

# modRana has the same sockettimeout set
import socket

timeout = 30 # this sets timeout for all sockets
socket.setdefaulttimeout(timeout)

path = '/tmp/'
filename1 = 'modRana_test_i_connectivity_google.gif'
filename2 = 'modRana_test_i_connectivity_osm.png'
google = 'http://www.google.com/intl/en_ALL/images/logo.gif'
osm = 'http://b.tile.openstreetmap.org/17/71964/44884.png'

print("###################################")
print("\n###testing internet connectivity###")
print("\n###################################")

print("\n1. trying to download Google logo to /tmp/ using urllib")
print("(%s)" % google)
try:
    urllib.urlretrieve(google, path + "urllib_" + filename1)
    print("OK: Google logo + urllib")
except Exception:
    import sys

    e = sys.exc_info()[1]
    print("error while downloading Google logo using urllib: %s" % e)

print("\n2. trying to download an OSM tile to /tmp/ using urllib")
print("(%s)" % osm)
try:
    urllib.urlretrieve(osm, path + "urllib_" + filename2)
    print("OK: OSM tile + urllib")
except Exception:
    import sys

    e = sys.exc_info()[1]
    print("error while downloading an OSM tile using urllib: %s" % e)

print("\n3. trying to download Google logo to /tmp/ using urllib2")
print("(%s)" % google)
try:
    req1 = urllib2.Request(google)
    reply1 = urllib2.urlopen(req1)
    string1 = path + "urllib2_" + filename1
    file1 = open(string1, 'w')
    file1.write(reply1.read())
    file1.close()
    print("OK: Google logo + urllib2")
except Exception:
    import sys

    e = sys.exc_info()[1]
    print("error while downloading Google logo using urllib2: %s" % e)

print("\n4. trying to download an OSM tile to /tmp/ using urllib2")
print("(%s)" % osm)
try:
    req2 = urllib2.Request(osm)
    reply2 = urllib2.urlopen(req2)
    string2 = path + "urllib2_" + filename2
    file2 = open(string2, 'w')
    file2.write(reply2.read())
    file2.close()
    print("OK: OSM tile + urllib2")
except Exception:
    import sys

    e = sys.exc_info()[1]
    print("error while downloading an OSM tile using urllib2: %s" % e)

print("\n 5. trying to download an OSM tile using proxy:")

# thanks to Slocan from http://talk.maemo.org/showthread.php?t=50570 for this testing code
# Slocan reports, that he is setting proxy in his N900 application FeedingIt like this without problems
def getProxy():
    import gconf

    if gconf.client_get_default().get_bool('/system/http_proxy/use_http_proxy'):
        port = gconf.client_get_default().get_int('/system/http_proxy/port')
        http = gconf.client_get_default().get_string('/system/http_proxy/host')
        proxy = proxy = urllib2.ProxyHandler({"http": "http://%s:%s/" % (http, port)})
        return True, proxy
    return False, None

# Enable proxy support
(proxy_support, proxy) = getProxy()
if proxy_support:
    opener = urllib2.build_opener(proxy)
    urllib2.install_opener(opener)

### Use urllib2.urlopen("http://...")
try:
    f = urllib2.urlopen(osm)
    data = f.read()
    f.close()
    string3 = path + "proxy_" + filename2
    file3 = open(string3, 'w')
    file3.write(data)
    file3.close()
    print("OK: OSM tile + proxy")
except Exception:
    import sys

    e = sys.exc_info()[1]
    print("error while downloading an OSM tile using proxy: %s" % e)

print("\n######################")
print("\n###testing complete###")
print("\n######################")

