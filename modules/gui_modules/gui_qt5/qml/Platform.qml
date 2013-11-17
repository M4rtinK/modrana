import QtQuick 2.0

Item {
    property string modRanaVersion :
    rWin.python.call_sync("modrana.gui.getModRanaVersion", [])

    property bool showQuitButton :
    rWin.python.call_sync("modrana.dmod.needsQuitButton", [])

    property bool fullscreenOnly :
    rWin.python.call_sync("modrana.dmod.fullscreenOnly", [])
}