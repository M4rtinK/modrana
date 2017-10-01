//ScaleBar.qml
//
// A scale bar useful to give map a scale.

import QtQuick 2.0
import UC 1.0
import "../functions.js" as F

Item {
    id : scaleBar
    property real lengthPixels : 0
    property real lengthMeters : 0
    property real tileScale : 1
    width : lengthPixels

    Rectangle {
        id: scaleBarRectangle
        color: "black"
        border.width: rWin.c.style.map.scaleBar.border
        border.color: "white"
        smooth: false
        height: rWin.c.style.map.scaleBar.height
        width: parent.width
    }
    Label {
        id: scaleBarText
        text: F.formatDistance(scaleBar.lengthMeters, scaleBar.tileScale)
        anchors.horizontalCenter: scaleBar.horizontalCenter
        anchors.top: scaleBar.bottom
        anchors.topMargin: rWin.c.style.main.spacing
        style: Text.Outline
        styleColor: "white"
        font.pixelSize: rWin.c.style.map.scaleBar.fontSize
    }
}