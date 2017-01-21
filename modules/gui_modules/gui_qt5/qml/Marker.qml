import QtQuick 2.0

Rectangle {
    id: marker
    width: 20 * rWin.c.style.m
    height: 20 * rWin.c.style.m
    property var targetPoint
    property var point
    x: targetPoint[0] - width/2
    y: targetPoint[1] - height/2
    border.width: 3 * rWin.c.style.m
    border.color: point.highlight ? "red" : "blue"
    radius: 7 * rWin.c.style.m
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
