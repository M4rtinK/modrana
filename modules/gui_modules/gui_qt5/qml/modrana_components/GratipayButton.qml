//GratipayButton.qml

import QtQuick 2.0
import UC 1.0

Rectangle {
    id : gpButton
    color : "#0D4035"
    gradient: Gradient {
        GradientStop { position: 0.0; color : "#2A8F79" }
        GradientStop { position: 1.0; color : "#0D4035" }
    }
    radius : 5
    smooth : true
    width : 150 * rWin.c.style.m
    // height should be slightly smaller than for the flattr button
    height : rWin.c.style.button.generic.height * 0.8
    property string url : ""
    Rectangle {
        id : clickedBg
        anchors.fill : parent
        radius : parent.radius
        visible : gpMA.pressed
        color : "#0D4035"
        smooth : true
    }
    Label {
        anchors.horizontalCenter : parent.horizontalCenter
        anchors.verticalCenter : parent.verticalCenter
        text : "<b>Gratipay</b>"
        color : "white"
        font.pixelSize : 24 * rWin.c.style.m
    }
    MouseArea {
        id : gpMA
        anchors.fill : parent
        onClicked : {
            rWin.log.info('Gratipay button clicked')
            Qt.openUrlExternally(url)
        }
    }
}


