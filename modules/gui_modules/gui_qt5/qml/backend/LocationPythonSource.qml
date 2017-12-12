// LocationPythonSource.qml
// used as a data transfer position source element if
// for location data from a Python side position source
import QtQuick 2.0

Item {
    id : fakeLocationSource
    property bool active : true
    property int updateInterval : 1000
    property string nmeaSource
    property string provider : "Python position provider"
    property bool valid : true
    property var position: Item {
        property bool altitudeValid : true
        property var coordinate : Coordinate {
            // Brno
            latitude : 49.2
            longitude : 16.616667
            altitude : 237.0
        }
        property real horizontalAccuracy : 0.0
        property bool horizontalAccuracyValid : true
        property bool latitudeValid : true
        property bool longitudeValid : true
        property real speed: 0.0
        property bool speedValid : true
        property real verticalSpeed : 0.0
        property bool verticalSpeedValid : true
        property real direction : 0.0
        property bool directionValid : false
        property real magneticVariation : 0.0
        property bool magneticVariationValid : true
        property date timestamp
        property real verticalAccuracy : 0.0
        property bool verticalAccuracyValid : true
    }
}