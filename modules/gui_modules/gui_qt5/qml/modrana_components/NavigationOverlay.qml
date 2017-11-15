//NavigationOverlay.qml

// Not really a full screen overlay, but stile meant to overlay the top
// of the map screen with slight transparency.

import QtQuick 2.0
import UC 1.0
import "../functions.js" as F

Rectangle {
    id : nbr
    color : "#92aaf3" // TODO: theming
    opacity : 0.85
    property int nMargin : Math.min(width/10.0, height/10.0)
    property int lMargin : nMargin * 10
    property int lColumnWidth : lMargin - 3 * nMargin
    property string message : ""
    property real distanceFromStep : -1
    property string iconId : ""
    Label {
        id : stepDistanceLabel
        visible : distanceFromStep != -1
        text : visible ? F.formatDistance(distanceFromStep, 1) : ""
        fontSizeMode : Text.Fit
        font.pixelSize: parent.height / 2.0 - 2 * nbr.nMargin
        verticalAlignment : Text.AlignTop
        width : nbr.lColumnWidth
        anchors.top : nbr.top
        anchors.topMargin : nMargin
        anchors.left : nbr.left
        anchors.leftMargin : nMargin
    }
    Image {
        id : stepIcon
        visible : nbr.iconId != ""
        source : visible ? "../navigation_icons/" + iconId + ".svg" : ""
        sourceSize.height: parent.height / 2.0 - nbr.nMargin
        sourceSize.width : nbr.lColumnWidth
        width : nbr.lColumnWidth
        fillMode : Image.PreserveAspectFit
        anchors.bottom : nbr.bottom
        anchors.bottomMargin : nMargin
        anchors.left : nbr.left
        anchors.leftMargin : nMargin
    }

    Label {
        id : messageLabel
        text : nbr.message
        verticalAlignment : Text.AlignVCenter
        horizontalAlignment : (lineCount == 1) ? Text.AlignHCenter : Text.AlignLeft
        width : parent.width - nbr.lMargin - nbr.nMargin
        height : parent.height - 2 * nbr.nMargin
        fontSizeMode : Text.Fit
        font.pixelSize: height / 2.0
        wrapMode : Text.WordWrap
        anchors.top : nbr.top
        anchors.topMargin : nMargin
        anchors.bottom : nbr.bottom
        anchors.bottomMargin : nMargin
        anchors.left : nbr.left
        anchors.leftMargin : lMargin
        anchors.right : nbr.right
        anchors.rightMargin : nMargin
    }
}
