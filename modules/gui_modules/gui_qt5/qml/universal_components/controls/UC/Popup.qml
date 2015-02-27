import QtQuick 2.0
import "style.js" as S

MouseArea {
    id: popup
    anchors.top: parent.top
    anchors.horizontalCenter: parent.horizontalCenter
    width: parent.width
    height: message.paintedHeight + (S.style.main.spacingBig * 1)
    property alias title: message.text
    property alias timeout: hideTimer.interval
    property alias background: bg.color
    visible: opacity > 0
    opacity: 0.0

    property color _defaultColor : "orange"

    Behavior on opacity {
        // the FadeAnimation silica equals to this
        NumberAnimation {
            duration: 200
            easing.type: Easing.InOutQuad
            property: "opacity"
        }
    }

    Rectangle {
        id: bg
        anchors.fill: parent
    }

    Timer {
        id: hideTimer
        triggeredOnStart: false
        repeat: false
        interval: 5000
        onTriggered: popup.hide()
    }

    function hide() {
        if (hideTimer.running)
            hideTimer.stop()
        popup.opacity = 0.0
    }

    function show() {
        popup.opacity = 1.0
        hideTimer.restart()
    }

    function notify(text, color) {
        popup.title = text
        if (color && (typeof(color) != "undefined"))
            bg.color = color
        else
            bg.color = Qt.rgba(_defaultColor.r, _defaultColor.g, _defaultColor.b, 0.9)
        show()
    }

    Label {
        id: message
        anchors.verticalCenter: popup.verticalCenter
        font.pixelSize: 32
        anchors.left: parent.left
        anchors.leftMargin: S.style.spacingBig
        anchors.right: parent.right
        anchors.rightMargin: S.style.spacing
        horizontalAlignment: Text.AlignHCenter
        elide: Text.ElideRight
        wrapMode: Text.Wrap
    }

    onClicked: hide()
}
