import QtQuick 1.1
import com.nokia.meego 1.0

Page {
    id : iconGP
    property double iconMargin : width/50.0
    property double iconSize : width/8.0

    // main "escape" button
    Button {
        anchors.top : parent.top
        anchors.left : parent.left
        anchors.leftMargin : iconMargin
        anchors.topMargin : iconMargin
        width : iconGP.iconSize
        height : iconGP.iconSize
        iconSource: "image://theme/icon-m-common-previous"
        opacity : 0.55
        onClicked : {
            rWin.pageStack.pop()
        }
    }

    // main flickable with icon grid
    Flickable {
        Grid {
            anchors.fill : parent
            anchors.margins : iconGP.iconMargin
            columns : 8
            spacing : iconGP.iconMargin
            //spacing : 10
            Button {
                width : iconGP.iconSize
                height : iconGP.iconSize
            }
            Button {
                width : iconGP.iconSize
                height : iconGP.iconSize
            }
            Button {
                width : iconGP.iconSize
                height : iconGP.iconSize
            }
            Button {
                width : iconGP.iconSize
                height : iconGP.iconSize
            }
        }
    }
}