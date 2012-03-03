import QtQuick 1.1
import com.nokia.meego 1.0

Page {

    property double iconMargin : width/50.0
    property double iconSize : width/8.0

    // main "escape" button
    Button {
        anchors.top : parent.top
        anchors.left : parent.left
        anchors.leftMargin : iconMargin
        anchors.topMargin : iconMargin
        width : parent.iconSize
        height : parent.iconSize
        iconSource: "image://theme/icon-m-common-previous"
        opacity : 0.55
        onClicked : {
            rWin.pageStack.pop()
        }


    }
}