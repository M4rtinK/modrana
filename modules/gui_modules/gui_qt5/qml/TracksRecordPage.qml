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
    property string realTracklogFolder : rWin.dcall("modrana.gui.modrana.paths.getTracklogsFolderPath",
                                         [], "unknown", function(v){realTracklogFolder = v})
    property string tracklogFolder : symlinkSwitch.checked ? "~/Documents/modrana_tracklogs" : rtPage.realTracklogFolder
    property string recordingText : rtPage.paused ? qsTr("Tracklog recording paused") : qsTr("Recording a tracklog")

    onPausedChanged : {
        if (recording) {
            if (paused) {
                rWin.log.info("TracksRecord: pausing recording")
                rWin.python.call("modrana.gui.modules.tracklog.pauseLogging", [], function(){
                    rWin.log.info("TracksRecord: recording paused")
                })
            } else {
                rWin.log.info("TracksRecord: unpausing recording")
                rWin.python.call("modrana.gui.modules.tracklog.unPauseLogging", [], function(){
                    rWin.log.info("TracksRecord: recording unpaused")
                })
            }
        } else {
            rWin.log.error("TracksRecord: can't pause/unpause when not recording")
        }
    }

    onRecordingChanged : {
        if (recording) {
            rWin.log.info("TracksRecord: starting recording")
            // first save the tracklog name to the options key,
            // then start logging from the callback once the key is set
            rWin.set("logNameEntry", tracklogNameField.text, function(){
                rtPage.startRecording()
            })
        } else {
            rWin.log.info("TracksRecord: stopping recording")
            rWin.python.call("modrana.gui.modules.tracklog.stopLogging", [], function(){
                rWin.log.info("TracksRecord: recording stopped")
                tracklogNameField.text = ""
                // we are done, remove the wake lock we added when we started
                // recording the track log
                rWin.keepAlive.removeWakeLock("tracklog_recording")
            })
        }
    }

    function startRecording() {
        // set a wake lock so that the device suspend does not ruin
        // our track logging attempt
        // TODO: report if suspend inhibition is not supported
        rWin.keepAlive.addWakeLock("tracklog_recording")
        rWin.python.call("modrana.gui.modules.tracklog.startLogging", [tracklogNameField.text], function(v){
            rWin.log.info("TracksRecord: recording started to file: " + v)
            tracklogNameField.text = v
        })
    }

    content : ContentColumn {
        id : contentC
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
        Label {
            text: qsTr("Recorded tracklogs folder:") + newline + rtPage.tracklogFolder + "/logs"
            property string newline : rWin.inPortrait ? "<br>" : " "
            //wrapMode : Text.WrapAnywhere
            wrapMode : Text.WrapAnywhere
            width : contentC.width
        }
        TextSwitch {
            // provide an easy way to create and remove a link from ~/Documents to the
            // modRana tracklogs folder location to make tracklogs more easily available to users
            id : symlinkSwitch
            visible : rWin.platform.sailfish
            text : qsTr("Symlink tracklogs to Documents")
            checked : false

            Component.onCompleted : {
                if (rWin.platform.sailfish) {
                    rWin.python.call("modrana.gui.tracklogs.sailfishSymlinkExists", [],
                                     function(v) {
                                        symlinkSwitch.checked = v
                                     })
                }
            }
            onCheckedChanged : {
                if (symlinkSwitch.visible) {
                    if (checked) {
                        rWin.python.call("modrana.gui.tracklogs.createSailfishSymlink", [])
                    } else {
                        rWin.python.call("modrana.gui.tracklogs.removeSailfishSymlink", [])
                    }
                }
            }
        }
    }
}