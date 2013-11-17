import QtQuick 2.0

//import "uiconstants.js" as UI

Rectangle {
    width: 10
    height: 10
    property variant coordinate
    property variant targetPoint
    property int verticalSpacing
    property bool showTextTop
    x: targetPoint[0] - width/2
    y: targetPoint[1] - height/2
    border.width: 3
    border.color: "#88ff00ff"
    radius: 7
    Text {
        anchors.left: parent.right
        anchors.leftMargin: 12
        y: (24 * verticalSpacing) - 12
        text: coordinate.name
        style: Text.Outline
        styleColor: "white"
        font.pixelSize: 24
    }
}
