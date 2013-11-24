// FakePosition.qml
// used as dummy position source element if
// the regular position source is not available
// for one reason or another

Item {
    id : fakeLocationSource
    property bool active : true
    property int interval : 1000
    property string nmeaSource
    property string provider : "fake position provider"
    property variant position: Item {
        property bool altitudeValid : false
        property variant coordinate : Coordinate {
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
        property date timestamp : null
        property real verticalAccuracy : 0.0
        property bool verticalAccuracyValid : false
    }
}