// Location.qml
// modRana QML module for location handling

import QtQuick 2.0

import "../functions.js" as F

Item {
    id : location
    property var locationSource
    property bool initialized : false
    // enabled tracks if location usage is enabled
    property bool usageEnabled : true

    property var _lastCoords : []

    property var _pythonSource : LocationPythonSource {}

    // connect to the location source position update signals
    Connections {
        id : locationUpdateConnection
        target : null
        onPositionChanged: positionUpdate(locationSource)
    }

    function positionUpdate(locationSource) {
        // use local variables both for readability and to hopefully make
        // the updates atomic in case that the source itself changes when
        // we are in the middle of an update
        var position = locationSource.position
        var coord = position.coordinate
        var sourceValid = locationSource.valid
        if (rWin.locationDebug.value) {
            rWin.log.debug("== Position update ==")
            rWin.log.debug("Coordinate:", coord.longitude, coord.latitude)
            rWin.log.debug("Speed:", position.speed)
            rWin.log.debug("Vertical speed:", position.verticalSpeed)
            rWin.log.debug("direction:", position.direction)
            rWin.log.debug("h/v accuracy:", position.horizontalAccuracy, position.verticalAccuracy)
            rWin.log.debug("timestamp: ", position.timestamp)
        }
        rWin.position = position
        rWin.pos = coord
        rWin.hasFix = sourceValid
        if (coord.isValid) {
            // replace the last good pos if lat & lon are valid
            rWin.lastGoodPos = coord
            // get the direction of travel
            // (as QML position info seems to be missing the direction
            // attribute, we need to compute it like this)
            location._addCoord(coord)
            rWin.bearing = location._getBearing()
            //rWin.log.debug("BEARING: " + rWin.bearing)
        }
        // tell the position to Python
        var posDict = {
            latitude : coord.latitude,
            longitude : coord.longitude,
            elevation : coord.altitude,
            speedMPS : position.speed
        }
        rWin.python.call("modrana.gui.setPosition", [posDict])
    }

    function _addCoord(coord) {
        // add the current position coordinate to an array so that it can be used
        // together with the previous coordinate to compute current bearing
        // (the QtPositioning QML interface really needs to fix the missing bearing property
        //  that the C++ interface has..)

        // push() returns new array length
        if (_lastCoords.push([coord.latitude,coord.longitude]) > 2) {
            // shift the oldest point out of the array
            _lastCoords.shift()
        }
    }

    function _getBearing() {
        // compute current bearing by computing the bearing between the current
        // and previous coordinates
        if (_lastCoords.length) {
            var first = _lastCoords[0]
            var last = _lastCoords[_lastCoords.length-1]
            return F.getBearingTo(first[0], first[1], last[0], last[1])
        } else {
            rWin.log.error("location: no coordinates, can't get bearing")
            return 0
        }
    }

    // location module initialization
    function __init__() {
        // first try to restore last known saved position
        var lastKnownPos = rWin.platform.lastKnownPos
        // check if location is enabled
        location.usageEnabled = rWin.platform.gpsEnabled
        // the pos key holds the (lat, lon) tuple
        if (lastKnownPos) {
            var savedCoord = rWin.loadQMLFile("backend/Coordinate.qml")
            savedCoord.latitude = lastKnownPos[0]
            savedCoord.longitude = lastKnownPos[1]
            rWin.lastGoodPos = savedCoord
            rWin.log.info("Qt5 location: saved position restored")
        }
        // try to load the location source
        // conditional imports would be nice, wouldn't they ;)
        var location_element = rWin.loadQMLFile("backend/LocationSource.qml", {}, true)
        if (location_element) {
            rWin.log.info("Qt5 location initialized")
        } else {
            // initializing the real source failed (Qt<5.2 ?),
            // use fake source instead
            rWin.log.error("Qt5 position source init failed (Qt<5.2 ?)")
            location_element = rWin.loadQMLFile("backend/LocationFakeSource.qml")
            // do an initial update so that Python code also gets the fake
            // position, which will not change anyway
            positionUpdate(location_element)
        }
        locationSource = location_element
        // connect the location update signal when we finally have the element
        locationUpdateConnection.target = locationSource
        // check if NMEA file source should be used
        var posFromFile = (rWin.platform.posFromFile == "NMEA")
        var NMEAFilePath = rWin.platform.nmeaFilePath
        // check if NMEA file should be used as position source
        // (useful for debugging without real positioning source)
        if (posFromFile && NMEAFilePath) {
            rWin.log.debug("Qt5 GUI: using NMEA file as position source")
            rWin.log.debug("NMEA file path: " + NMEAFilePath)
            locationSource.nmeaSource = NMEAFilePath
            // if the nmeaSource is on an initialized PositionSource,
            // the update interval needs to be reset, or it is ignored
            // TODO: fill bug report to Qt Project
            locationSource.updateInterval = 1000
        }
        // report which position provider is being used
        rWin.log.info("Qt5 GUI location provider: " + locationSource.provider)
        // initialization complete
        location.initialized = true
        // start location
        // TODO: check if location should be started
        location.start()
    }

    // start location
    function start() {
        if (location.enabled) {
            if (location.initialized) {
                locationSource.active = true
            } else {
                rWin.log.error("Qt5 location: can't start, not initialized")
            }
        } else {
            rWin.log.info("Qt5 location: location usage disabled by user")
        }
    }

    // stop location
    function stop() {
        if (location.initialized) {
            locationSource.active = false
        } else {
            rWin.log.error("Qt5 location: can't stop, not initialized")
        }
    }

    Component.onCompleted : {
        // on some platforms the position source could be on the
        // Python side, such as GPSD
        rWin.python.setHandler("pythonPositionUpdate", function(update) {
            _pythonSource.valid = update.valid
            if (update.altitude != null) {
                _pythonSource.position.altitudeValid = true
                _pythonSource.position.coordinate.altitude = update.altitude
            } else {
                _pythonSource.position.altitudeValid = false
            }
            _pythonSource.position.coordinate.latitude = update.latitude
            _pythonSource.position.coordinate.longitude = update.longitude
            _pythonSource.position.horizontalAccuracy = update.horizontalAccuracy
            _pythonSource.position.verticalAccuracy = update.verticalAccuracy
            _pythonSource.position.speed = update.speed
            _pythonSource.position.verticalSpeed = update.verticalSpeed
            _pythonSource.position.direction = update.direction
            _pythonSource.position.magneticVariation = update.magneticVariation
            _pythonSource.position.magneticVariationValid = update.magneticVariationValid
            _pythonSource.position.timestamp = update.timestamp
            positionUpdate(_pythonSource)
        })
    }
}
