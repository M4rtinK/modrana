// QtQuick timer designed for dynamic runtime creation and triggering
import QtQuick 2.0

Timer {
    id : dynamicTimer
    property int timerId
    running : true
    repeat : true

    onTriggered : {
        rWin.python.call("modrana.gui.modules.cron._timerTriggered", [dynamicTimer.timerId])
    }
}