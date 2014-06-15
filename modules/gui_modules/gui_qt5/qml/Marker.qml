import QtQuick 2.0

Rectangle {
    id: marker
    width: 20
    height: 20
    property variant targetPoint
    property variant point
    x: targetPoint[0] - width/2
    y: targetPoint[1] - height/2
    border.width: 3
    border.color: point.highlight ? "red" : "blue"
    radius: 7
    // the "simple mode" is used usually on higher zoom
    // levels to avoid label clutter as only the the marker
    // and not the label is drawn when it is enabled
    property bool simple : false
    Text {
        id: label
        visible: !marker.simple
        anchors.left: parent.right
        anchors.leftMargin: 12
        anchors.verticalCenter : parent.verticalCenter
        text: point.name
        style: Text.Outline
        styleColor: "white"
        font.pixelSize: 24
    }
}
