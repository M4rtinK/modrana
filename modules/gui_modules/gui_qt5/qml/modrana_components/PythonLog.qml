//PythonLog.qml
// A QML element that provides Python style logging to QML
// a forwards the log messages to the Python log.

import QtQuick 2.0

Item {
    id : pythonLogger
    property bool backendAvailable : false

    function debug(message) {
        if (pythonLogger.backendAvailable) {
            rWin.python.call("modrana.gui.qml_log.debug", ["" + message])
        } else {
            console.log("DEBUG: " + message)
        }
    }

    function info(message) {
        if (pythonLogger.backendAvailable) {
            rWin.python.call("modrana.gui.qml_log.info", ["" + message])
        } else {
            console.log("INFO: " + message)
        }
    }

    function warning(message) {
        if (pythonLogger.backendAvailable) {
            rWin.python.call("modrana.gui.qml_log.warning", ["" + message])
        } else {
            console.log("WARNING: " + message)
        }
    }

    function error(message) {
        if (pythonLogger.backendAvailable) {
            rWin.python.call("modrana.gui.qml_log.error", ["" + message])
        } else {
            console.log("ERROR: " + message)
        }
    }

    function critical(message) {
        if (pythonLogger.backendAvailable) {
            rWin.python.call("modrana.gui.qml_log.critical", ["" + message])
        } else {
            console.log("CRITICAL: " + message)
        }
    }
}
