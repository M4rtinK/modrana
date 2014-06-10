// Location.qml
// modRana QML module for location handling

import QtQuick 2.0

Item {
    id : location
    property variant locationSource
    property bool initialized : false
    // enabled tracks if location usage is enabled
    property bool usageEnabled : true

    property variant _lastCoord

    // connect to the location source position update signals
    Connections {
        id : locationUpdateConnection
        target : null
        onPositionChanged: positionUpdate(locationSource)
    }

    function positionUpdate(locationSource) {
        var coord = locationSource.position.coordinate
        console.log("position changed")
        console.log("Coordinate:", coord.longitude, coord.latitude)
        //console.log("Speed:", locationSource.position.speed)
        //console.log("h/v accuracy:", locationSource.position.horizontalAccuracy, locationSource.position.verticalAccuracy)
        rWin.position = locationSource.position
        rWin.pos = coord
        rWin.hasFix = locationSource.valid
        if (coord.isValid) {
            // replace the last good pos if lat & lon are valid
            rWin.lastGoodPos = locationSource.position.coordinate
            // get the direction of travel
            // (as QML position info seems to be missing the direction
            // attribute, we need to compute it like this)
            if (location._lastCoord) {
                rWin.bearing = location._lastCoord.azimuthTo(coord)
                //console.log("BEARING " + rWin.bearing)
            }
            // save the current coord for the next bearing
            // computation
            location._lastCoord = coord
        }
        // tell the position to Python
        var posDict = {
            latitude : locationSource.position.coordinate.latitude,
            longitude : locationSource.position.coordinate.longitude,
            elevation : locationSource.position.coordinate.altitude,
            speedMPS : locationSource.position.speed
        }
        rWin.python.call("modrana.gui.setPosition", [posDict])
    }


    // location module initialization
    function __init__() {
        // first try to restore last known saved position
        var lastKnownPos = rWin.get_sync("pos", null)
        // check if location is enabled
        location.usageEnabled = rWin.get_sync("GPSEnabled", true)
        // the pos key holds the (lat, lon) tuple
        if (lastKnownPos) {
            var savedCoord = rWin.loadQMLFile("Coordinate.qml")
            savedCoord.latitude = lastKnownPos[0]
            savedCoord.longitude = lastKnownPos[1]
            rWin.lastGoodPos = savedCoord
            console.log("Qt5 location: saved position restored")
        }
        // try to load the location source
        // conditional imports would be nice, wouldn't they ;)
        var location_element = rWin.loadQMLFile("LocationSource.qml", true)
        if (location_element) {
            console.log("Qt5 location initialized")
        } else {
            // initializing the real source failed (Qt<5.2 ?),
            // use fake source instead
            console.log("Qt5 position source init failed (Qt<5.2 ?)")
            location_element = rWin.loadQMLFile("LocationFakeSource.qml")
            // do an initial update so that Python code also gets the fake
            // position, which will not change anyway
            positionUpdate(location_element)
        }
        locationSource = location_element
        // connect the location update signal when we finally have the element
        locationUpdateConnection.target = locationSource
        // check if NMEA file source should be used
        var posFromFile = (rWin.get_sync("posFromFile", "") == "NMEA")
        var NMEAFilePath = rWin.get_sync("NMEAFilePath", "")
        // check if NMEA file should be used as position source
        // (useful for debugging without real positioning source)
        if (posFromFile && NMEAFilePath) {
            console.log("Qt5 GUI: using NMEA file as position source")
            console.log("NMEA file path: " + NMEAFilePath)
            locationSource.nmeaSource = NMEAFilePath
            // if the nmeaSource is on an initialized PositionSource,
            // the update interval needs to be reset, or it is ignored
            // TODO: fill bug report to Qt Project
            locationSource.updateInterval = 1000
        }
        // report which position provider is being used
        console.log("Qt5 GUI location provider: " + locationSource.provider)
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
                console.log("Qt5 location: can't start, not initialized")
            }
        } else {
            console.log("Qt5 location: location usage disabled by user")
        }
    }

    // stop location
    function stop() {
        if (location.initialized) {
            locationSource.active = false
        } else {
            console.log("Qt5 location: can't stop, not initialized")
        }
    }
}