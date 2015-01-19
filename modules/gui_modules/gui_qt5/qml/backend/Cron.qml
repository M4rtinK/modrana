// Runtime timer management for use from Python
//
// Python does not have an easy access to the Qt 5 main loop, so provide
// an interface for it to easy register timer on the QML side.
// The timers can be added, removed or their timeout changed.
// When a timer triggers, it sends a signal with ist timer id to Python
// over PyOtherSide, which is then handled by the modRana cron module and
// translated to the Python callback that was set when the timer was registered
// on the Python side.

import QtQuick 2.0

Item {
    id : cron
    property var timers : new Object()

    function addTimer(timerId, timeout) {
        // add a timer with the given timeout, start it and add it to the
        // timer tracking dictionary
        var newTimer = Qt.createQmlObject('import QtQuick 2.0; DynamicTimer {}', cron)
        newTimer.timerId = timerId
        newTimer.interval = timeout
        cron.timers[timerId] = newTimer
        rWin.log.debug("cron: timer added, timeout: " + timeout + " id: " + timerId)
    }

    function removeTimer(timerId) {
        // stop a timer and remove it from the timer tracking dictionary
        cron.timers[timerId].stop()
        delete cron.timers[timerId]
        rWin.log.debug("cron: timer removed: " + timerId)
    }

    function modifyTimerTimeout(self, timeoutId, newTimeout) {
        // modify the duration of a timer in progress"""
        cron.timers[timerId].interval = newTimeout
        rWin.log.debug("cron: timer " + timerId + " has new timeout: " + newTimeout)
    }

    Component.onCompleted : {
        rWin.python.setHandler("addTimer", addTimer)
        rWin.python.setHandler("removeTimer", removeTimer)
        rWin.python.setHandler("modifyTimerTimeout", modifyTimerTimeout)
    }
}