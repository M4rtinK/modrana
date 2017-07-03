// Keep alive control - keep device awake even if it would normally suspend.
// This functionality is needed so that features like track logging, batch tile downloading
// or turn by turn navigation work correctly.

import QtQuick 2.0

Item {
    id : stillAlive

    property var keepAliveInstance : null
    property var _wakeLocks : []
    property bool keepAlive : false
    property bool available : keepAliveInstance != null

    onKeepAliveChanged : {
        if (stillAlive.keepAliveInstance != null) {
           stillAlive.keepAliveInstance.enabled = keepAlive
           if (keepAlive) {
               rWin.log.info("KeepAlive: keep alive enabled")
           } else {
               rWin.log.info("KeepAlive: keep alive disabled")
           }
        }
    }

    Component.onCompleted : {
        initKeepAlive()
    }

    function initKeepAlive() {
        // the keep-alive control module might not be available on
        // all platforms so we need to handle import failure
        // (real conditional imports would be nice, wouldn't they ;))
        // TODO: handle also other platforms than Sailfish OS
        var sailfishKeepAliveInstance = rWin.loadQMLFile("sailfish_specific/SailfishKeepAlive.qml", {}, true)
        if (sailfishKeepAliveInstance) {
            rWin.log.info("KeepAlive: keep alive control initialized")
            stillAlive.keepAliveInstance = sailfishKeepAliveInstance
        } else {
            rWin.log.info("KeepAlive: keep alive control is not available")
        }
    }

    function addWakeLock(wakeLockId) {
        rWin.log.info("KeepAlive: adding wake lock: " + wakeLockId)
        // check if the wake lock has already been registered
        var wakeLockIndex = stillAlive._wakeLocks.indexOf(wakeLockId)
        if (wakeLockIndex != -1) {
            rWin.log.warning("KeepAlive: wake lock " + wakeLockId + "already registered")
        } else {
            stillAlive._wakeLocks.push(wakeLockId)
            if (!stillAlive.keepAlive) {
                stillAlive.keepAlive = true
            }
        }
    }

    function removeWakeLock(wakeLockId) {
        var wakeLockIndex = _wakeLocks.indexOf(wakeLockId)
        if (wakeLockIndex == -1) {
            rWin.log.warning("KeepAlive: can't remove unknown wake lock: " + wakeLockId)
        } else {
            // lets hope this is always only called from a single thread ;-)
            stillAlive._wakeLocks.splice(wakeLockIndex,1)
            // disable keep alive in no wake locks remain
            if (stillAlive._wakeLocks.length == 0) {
                stillAlive.keepAlive = false
            }
        }
    }
}
