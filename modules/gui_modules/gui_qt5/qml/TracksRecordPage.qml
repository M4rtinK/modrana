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
    property string lastUsedTracklogName : rWin.get("logNameEntry", "", function(v){lastUsedTracklogName=v})

    property var currentStatus : {
        "speed" : {
            "current" : 0,
            "avg" : 0,
            "max" : 0
        },
        "distance" : 0,
        "elapsedTime" : 0,
        "pointCount" : 0
    }
    // report if the status dict has real data
    property bool statusValid : false

    onPausedChanged : {
        if (recording) {
            if (paused) {
                rWin.log.info("TracksRecord: pausing recording")
                rWin.mapPage.trackRecordingPaused = true
                rWin.python.call("modrana.gui.modules.tracklog.pauseLogging", [], function(){
                    rWin.log.info("TracksRecord: recording paused")
                })
            } else {
                rWin.log.info("TracksRecord: unpausing recording")
                rWin.mapPage.trackRecordingPaused = false
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
            lastUsedTracklogName = tracklogNameField.text
            // enabled trace drawing
            // (provided it was not turned off by the switch)
            rWin.mapPage.drawTracklogTrace = drawTraceSwitch.checked
            rWin.set("logNameEntry", tracklogNameField.text, function(){
                rtPage.startRecording()
            })
        } else {
            rWin.log.info("TracksRecord: stopping recording")
            rWin.mapPage.drawTracklogTrace = false
            rWin.python.call("modrana.gui.modules.tracklog.stopLogging", [], function(){
                rWin.log.info("TracksRecord: recording stopped")
                tracklogNameField.text = rtPage.lastUsedTracklogName
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
            text : rtPage.lastUsedTracklogName
            readOnly : rtPage.recording
            anchors.horizontalCenter : parent.horizontalCenter
            inputMethodHints : Qt.ImhNoAutoUppercase | Qt.ImhNoPredictiveText
            width : parent.width
            onFocusChanged : {
                if (focus) {
                    selectAll()
                }
            }
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
        SmartGrid {
            id : statusGrid
            visible : rtPage.statusValid
            Label {
                text: qsTr("<b>current speed:</b>") + " " + rtPage.currentStatus.speed.current
                width : statusGrid.cellWidth
            }
            Label {
                text: qsTr("<b>average speed:</b>") + " " + rtPage.currentStatus.speed.avg
                width : statusGrid.cellWidth
            }
            Label {
                text: qsTr("<b>max speed:</b>") + " " + rtPage.currentStatus.speed.max
                width : statusGrid.cellWidth
            }
            Label {
                text: qsTr("<b>distance:</b>") + " " + rtPage.currentStatus.distance
                width : statusGrid.cellWidth
            }
            Label {
                text: qsTr("<b>elapsed time:</b>") + " " + rtPage.currentStatus.elapsedTime
                width : statusGrid.cellWidth
            }
            Label {
                text: qsTr("<b>points:</b>") + " " + rtPage.currentStatus.pointCount
                width : statusGrid.cellWidth
            }
        }

        Label {
            text: qsTr("Recorded tracklogs folder:") + newline + rtPage.tracklogFolder + "/logs"
            property string newline : rWin.inPortrait ? "<br>" : " "
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
            property bool readyForUse : false

            Component.onCompleted : {
                if (rWin.platform.sailfish) {
                    rWin.python.call("modrana.gui.tracklogs.sailfishSymlinkExists", [],
                                     function(v) {
                                        symlinkSwitch.checked = v
                                        readyForUse = true
                                     })
                }
            }
            onCheckedChanged : {
                // ignore changes to the checked property until the switch is ready for use
                // - that means that we are on Sailfish OS and that we have checked if the
                //   symlink exists or not
                if (readyForUse) {
                    if (checked) {
                        rWin.python.call("modrana.gui.tracklogs.createSailfishSymlink", [])
                    } else {
                        rWin.python.call("modrana.gui.tracklogs.removeSailfishSymlink", [])
                    }
                }
            }
        }
        KeyTextSwitch {
            id : drawTraceSwitch
            text : qsTr("Draw logging trace")
            key : "drawTracklogTrace"
            defaultValue : true
            onCheckedChanged : {
                rWin.mapPage.drawTracklogTrace = checked
            }
        }
        Label {
            text : qsTr("Trace opacity")
            visible : drawTraceSwitch.checked
        }
        Slider {
            id : traceOpacitySlider
            width : parent.width
            stepSize : 0.1
            value : rWin.mapPage.tracklogTraceOpacity
            valueText : ""
            visible : drawTraceSwitch.checked
            onPressedChanged : {
                // set the value once users
                // stops interacting with the slider
                if (pressed == false) {
                    rWin.mapPage.tracklogTraceOpacity = value
                    rWin.set("qt5GUITracklogTraceOpacity", value)
                }
            }
        }


    }

    Component.onCompleted : {
        rWin.python.setHandler("tracklogUpdated", function(update) {
            rtPage.statusValid = true
            rtPage.currentStatus = update
        })
    }

    onIsActiveChanged : {
        if (isActive) {
            rWin.python.call("modrana.gui.tracklogs.setSendUpdates", [true])
        } else {
            rWin.python.call("modrana.gui.tracklogs.setSendUpdates", [false])
        }
    }

}
