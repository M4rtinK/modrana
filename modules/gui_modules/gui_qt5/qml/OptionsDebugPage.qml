//OptionsDebugPage.qml

import QtQuick 2.0
import UC 1.0
import "modrana_components"
import "backend"

BasePage {
    id: debugPage
    headerText : qsTr("Debug")

    property alias logFileEnabled: logFileEnabledProp.value
    OptProp {id: logFileEnabledProp; key : "loggingStatus"; value : false}

    property alias logFileCompression: logFileCompressionProp.value
    OptProp {id: logFileCompressionProp; key : "compressLogFile"; value : false}

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
        SectionHeader {
            text : qsTr("Show what is hidden")
        }
        TextSwitch {
            text : qsTr("Show debug button")
            checked : rWin.showDebugButton
            onCheckedChanged : {
                 rWin.showDebugButton = checked
            }
        }
        TextSwitch {
            text : qsTr("Show unfinished features")
            checked : rWin.showUnfinishedFeatures
            onCheckedChanged : {
                rWin.showUnfinishedFeatures = checked
            }
        }
        SectionHeader {
            text : qsTr("Debugging messages")
        }
        TextSwitch {
            text : qsTr("Tile display debugging")
            checked : rWin.tileDebug
            onCheckedChanged : {
                rWin.tileDebug = checked
            }
        }
        TextSwitch {
            text : qsTr("Tile storage debugging")
            checked : rWin.tileStorageDebug
            onCheckedChanged : {
                rWin.tileStorageDebug = checked
            }
        }
        TextSwitch {
            text : qsTr("Location debugging")
            checked : rWin.locationDebug
            onCheckedChanged : {
                rWin.locationDebug = checked
            }
        }
        TextSwitch {
            text : qsTr("Map canvas debugging")
            checked : rWin.pinchmapCanvasDebug
            onCheckedChanged : {
                rWin.pinchmapCanvasDebug = checked
            }
        }
        SectionHeader {
            text : qsTr("Logging")
        }
        TextSwitch {
            text : qsTr("Log file")
            checked : logFileEnabled
            onCheckedChanged : {
                logFileEnabled = checked
            }
        }
        TextSwitch {
            text : qsTr("Log file compression")
            checked : logFileCompression
            onCheckedChanged : {
                logFileCompression = checked
            }
        }
        Label {
            text : debugPage.logFilePath
            wrapMode : Text.WrapAnywhere
            width : parent.width
        }
        SectionHeader {
            text : qsTr("Notifications")
        }
        Button {
            text : qsTr("Notify")
            onClicked : {
                rWin.notify(qsTr("Hello world!"))
            }
        }
        Button {
            text : qsTr("Notify long")
            onClicked : {
                rWin.notify(qsTr("This is modRana - a flexible navigation software for (not only) mobile Linux devices!"))
            }
        }
    }
}
