//InfoSpeedPage.qml

import QtQuick 1.1
import "qtc/PageStatus.js" as PageStatus
import "./qtc"

BasePage {
    id: locationPage
    headerText : "Location"
    bottomPadding : 0
    isFlickable : false
    //anchors.fill : parent

    content {
        Label {
            id : fixStatus
            anchors.top : parent.top
            anchors.topMargin : 24
            anchors.horizontalCenter : parent.horizontalCenter
            text: gps.mode == 3 ? "3D fix" : "2D fix"
            color: gps.mode == 3 ? "green" : "yellow"
            font.pixelSize : 32
            visible : gps.hasFix
        }
        Grid {
            anchors.top : fixStatus.bottom
            anchors.left : parent.left
            anchors.right : parent.right
            anchors.topMargin : 24
            visible : gps.hasFix
            /*
            Label {
                id : fixStatus1
                anchors.topMargin : 24
                //anchors.horizontalCenter : parent.horizontalCenter
                text: gps.mode == 3 ? "3D fix" : "2D fix"
                color: gps.mode == 3 ? "green" : "yellow"
                font.pixelSize : 32
            }*/
        }
        Label {
            id : noFixLabel
            visible : !gps.hasFix
            anchors.horizontalCenter : parent.horizontalCenter
            //anchors.verticalCenter : parent.verticalCenter
            anchors.top : parent.top
            anchors.topMargin : 24
            color : "red"
            font.pixelSize : 64
            text : "NO FIX"
        }
    }
}