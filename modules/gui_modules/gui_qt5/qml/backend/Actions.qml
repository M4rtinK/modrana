// defines various actions and registers their triggers
import QtQuick 2.0

Item {
    id : actions

    property bool mediaKeysEnabled : false

    signal zoomUp
    signal zoomDown

    property var mediaKeys : null

    // we need to handle the case where the MediaKeys element
    // is not available so we use the Connections a nd Binding
    // elements to work with it

    Connections {
        // this condition setting null prevents warnings if the media
        // keys element is not available
        target : actions.mediaKeys ? actions.mediaKeys : null

        onUp : {
            actions.zoomUp()
        }

        onDown : {
            actions.zoomDown()
        }
    }

    Binding {
        // this condition setting null prevents warnings if the media
        // keys element is not available
        target : actions.mediaKeys ? actions.mediaKeys : null
        property : "enabled"
        value : actions.mediaKeysEnabled && Qt.application.active
    }

    Component.onCompleted : {
        initMediaKeys()
    }

    function initMediaKeys() {
        // the media keys module might not be available on
        // all platforms so we need to handle import failure
        // (real conditional imports would be nice, wouldn't they ;))
        var mediaKeysInstance = rWin.loadQMLFile("sailfish_specific/SailfishMediaKeys.qml", {}, true)
        if (mediaKeysInstance) {
            rWin.log.info("Actions: Sailfish media keys initialized")
            actions.mediaKeys = mediaKeysInstance
        } else {
            rWin.log.info("Actions: media keys not available")
        }
    }
}
