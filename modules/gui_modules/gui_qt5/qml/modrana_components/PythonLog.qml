//PythonLog.qml
// A QML element that provides Python style logging to QML
// a forwards the log messages to the Python log.

import QtQuick 2.0

Item {
    id : pythonLogger

    function debug(message) {
        rWin.python.call("modrana.gui.qml_log.debug", [message])
    }

    function info(message) {
        rWin.python.call("modrana.gui.qml_log.info", [message])
    }

    function warning(message) {
        rWin.python.call("modrana.gui.qml_log.warning", [message])
    }

    function error(message) {
        rWin.python.call("modrana.gui.qml_log.error", [message])
    }

    function critical(message) {
        rWin.python.call("modrana.gui.qml_log.critical", [message])
    }
}
