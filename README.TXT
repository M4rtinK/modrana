# modRana #

ModRana is a flexible GPS navigation system for mobile Linux devices.

## Development ##

Pull requests welcome ! :D

## Devices ##
Confirmed to run on:
* desktop PCs
* Nokia N900
* Nokia N9 & N950
* Neo FreeRunner
* Smart Q7

## Dependencies ##

* Python 2.5+

### GTK GUI ###
* PyGTK
* PyCairo
* Python-Location (N900)

### QML GUI ###
* PySide & Qt 4.7.4+
* Qt Componnents
* python-mobility

## Ancestry ##

ModRana begin as a fork of the [Rana project](http://wiki.openstreetmap.org/wiki/Rana), but currently uses code from many open source projects:
* Upoints - GPX handling
* Odict - ordered dictionaries
* GPSD Python bindings
* AGTL - Fix object, PinchMap element
* geopy - Geonames access
* googlemaps - Google API
* configobj - configuration file handling
* PyCha - route profile graphs
* urllib3 - tile download connection reuse
* argparse standalone - startup argument handling

## Licence ##

ModRana is licenced under GPLv3.

## Resources ##

[modRana project website](http://www.modrana.org)
[discussion thread on talk.maemo.org](http://talk.maemo.org/showthread.php?t=58861)
