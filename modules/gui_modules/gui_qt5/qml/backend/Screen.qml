// defines various actions and registers their triggers
import QtQuick 2.0

Item {
    id : screen

    property bool keepScreenOn : false

    property var screenInstance : null

    onKeepScreenOnChanged : {
        if  (screenInstance != null) {
            screenInstance.suspend = keepScreenOn
            if (keepScreenOn) {
                rWin.log.info("screen blanking enabled")
            } else {
                rWin.log.info("screen blanking disabled")
            }
        }
    }

    Component.onCompleted : {
        initScreen()
    }

    function initScreen() {
        // the screen control module might not be available on
        // all platforms so we need to handle import failure
        // (real conditional imports would be nice, wouldn't they ;))
        // TODO: handle also other platforms than Sailfish OS
        var sailfishScreenInstance = rWin.loadQMLFile("sailfish_specific/SailfishScreen.qml", {}, true)
        if (sailfishScreenInstance) {
            rWin.log.info("Screen: screen blanking control initialized")
            screen.screenInstance = sailfishScreenInstance
        } else {
            rWin.log.info("Screen: screen blanking control is not available")
        }
    }
}
