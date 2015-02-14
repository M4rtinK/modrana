//Coordinate.qml
import QtQuick 2.0

Item {
    property real latitude
    property real longitude
    property real altitude
    property bool isValid : true

    function _toDeg (rad) {
        return rad * 180 / Math.PI;
    }

    function azimuthTo(coord){
        var dLon = (coord.longitude-longitude);
        var y = Math.sin(dLon) * Math.cos(coord.latitude);
        var x = Math.cos(latitude)*Math.sin(coord.latitude) - Math.sin(latitude)*Math.cos(coord.latitude)*Math.cos(dLon);
        var brng = _toDeg(Math.atan2(y, x));
        return 360 - ((brng + 360) % 360);
    }
}