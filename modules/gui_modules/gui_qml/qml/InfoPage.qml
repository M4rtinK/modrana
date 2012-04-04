import QtQuick 1.1
import com.nokia.meego 1.0

Page {

    Label {
        anchors.verticalCenter : parent.verticalCenter
        anchors.horizontalCenter : parent.horizontalCenter
        font.pixelSize : 64
        text : "modRana version:<br>" + platform.modRanaVersion()
        color:"white"
    }

    IconGridButton {
        iconSize : iconGP.iconSize
        margin : iconGP.iconMargin
        anchors.top : parent.top
        anchors.left : parent.left
        anchors.topMargin : iconGP.iconMargin/4.0
        iconName : "left_thin.png"
        text : "back"
        opacity : gridView.atYBeginning ? 1.0 : 0.55
        onClicked : {
            rWin.pageStack.pop()
        }
    }
}