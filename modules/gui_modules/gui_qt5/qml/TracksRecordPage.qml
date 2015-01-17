//TracksRecordPage.qml

import QtQuick 2.0
import UC 1.0
import "modrana_components"

BasePage {
    id: rtPage
    headerText : rtPage.recording ? recordingText : qsTr("Record a tracklog")
    property bool ready : true
    property bool recording : false
    property bool paused : false
    property string tracklogFolder : "unknown"
    property string recordingText : rtPage.paused ? qsTr("Tracklog recording paused") : qsTr("Recording a tracklog")

    onPausedChanged : {
        if (recording) {
            if (paused) {
                rWin.log.info("TracksRecord: pausing recording")
            } else {
                rWin.log.info("TracksRecord: unpausing recording")
            }
        } else {
            rWin.log.error("TracksRecord: can't pause/unpause when not recording")
        }
    }

    onRecordingChanged : {
        if (recording) {
            rWin.log.info("TracksRecord: starting recording")
        } else {
            rWin.log.info("TracksRecord: stopping recording")
        }
    }

    content : ContentColumn {
        TextField {
            id : tracklogNameField
            placeholderText: qsTr("Enter tracklog name here!")
            readOnly : rtPage.recording
            anchors.horizontalCenter : parent.horizontalCenter
            onTextChanged : {
                selectAll()
            }
            width : parent.width
        }
        Grid {
            id : buttonGrid
            columns : rWin.inPortrait ? 1 : 2
            spacing : rWin.c.style.main.spacing
            property real buttonWidth : rWin.inPortrait ? parent.width : (parent.width/2)-rWin.c.style.main.spacing
            Button {
                text : rtPage.recording ? qsTr("stop") : qsTr("start")
                width : buttonGrid.buttonWidth
                onClicked : {
                    rtPage.recording = !rtPage.recording
                    rtPage.paused = false
                }
            }
            Button {
                text : rtPage.paused ? qsTr("unpause") : qsTr("pause")
                width : buttonGrid.buttonWidth
                visible : rtPage.recording ? true : false
                onClicked :  rtPage.paused = !rtPage.paused
            }
        }
        Grid {
            id : folderGrid
            columns : rWin.inPortrait ? 1 : 2
            spacing : rWin.c.style.main.spacing
            Label {
                text: "Tracklogs folder:"
            }
            Label {
                text: "/blah/blah"
            }
        }
    }
}