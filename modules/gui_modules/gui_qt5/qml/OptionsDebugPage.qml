//OptionsDebugPage.qml

import QtQuick 2.0
import UC 1.0
import "modrana_components"
import "backend"

BasePage {
    id: debugPage
    headerText : "Debug"

    property variant logFileEnabled: OptProp {key : "loggingStatus"; value : false}

    property string logFilePath : setLogFilePath()

    function setLogFilePath() {
        rWin.python.call("modrana.gui.log_manager.get_log_file_path", [], function(v){
            if (v) {
                debugPage.logFilePath = v
            } else {
                debugPage.logFilePath = qsTr("log file disabled")
            }
    })
        return qsTr("log path unknown")
   }

    content : ContentColumn {
        TextSwitch {
            text : qsTr("Show debug button")
            checked : rWin.showDebugButton
            onCheckedChanged : {
                 rWin.showDebugButton = checked
                 rWin.set("showQt5GUIDebugButton", checked)
            }
        }
        TextSwitch {
            text : qsTr("Show unfinished pages")
            checked : rWin.showUnfinishedPages
            onCheckedChanged : {
                rWin.showUnfinishedPages = checked
                rWin.set("showQt5GUIUnfinishedPages", checked)
            }
        }
        TextSwitch {
            text : qsTr("Tile handling debugging")
            checked : rWin.tileDebug
            onCheckedChanged : {
                rWin.tileDebug = checked
                rWin.set("showQt5TileDebug", checked)
            }
        }
        TextSwitch {
            text : qsTr("Location debugging")
            checked : rWin.locationDebug
            onCheckedChanged : {
                rWin.locationDebug = checked
                rWin.set("gpsDebugEnabled", checked)
            }
        }
        Label {
            text : "Logging"
        }
        TextSwitch {
            text : qsTr("Log file")
            checked : logFileEnabled.value
            onCheckedChanged : {
                logFileEnabled.value = checked
            }
        }
        Label {
            text : debugPage.logFilePath
            wrapMode : Text.WrapAnywhere
            width : parent.width
        }
    }
}
