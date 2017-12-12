// FakePosition.qml
// used as dummy position source element if
// the regular position source is not available
// for one reason or another
import QtQuick 2.0

Item {
    id : fakeLocationSource
    property bool active : true
    property int updateInterval : 1000
    property string nmeaSource
    property string provider : "fake position provider"
    property bool valid : true
    property var position: Item {
        property bool altitudeValid : false
        property var coordinate : Coordinate {
            // Brno
            latitude : 49.2
            longitude : 16.616667
            altitude : 237.0
        }
        property real horizontalAccuracy : 0.0
        property bool horizontalAccuracyValid : false
        property bool latitudeValid : false
        property bool longitudeValid : false
        property real speed: 0.0
        property bool speedValid : false
        property real verticalSpeed : 0.0
        property bool verticalSpeedValid : false
        property real direction : 0.0
        property bool directionValid : false
        property real magneticVariation : 0.0
        property bool magneticVariationValid : false
        property date timestamp
        property real verticalAccuracy : 0.0
        property bool verticalAccuracyValid : false
    }
    Component.onCompleted: {
        rWin.position = fakeLocationSource.position
        rWin.pos = fakeLocationSource.position.coordinate
    }
}