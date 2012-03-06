import QtQuick 1.1
import com.nokia.meego 1.0

Page {
    id : iconGP
    property double iconMargin : width/20.0
    property double iconSize : (width-2)/5.0
    // search, routes, POI, mode, options, info

    ListModel {
        id : testModel

        ListElement {
            caption : ""
            icon : ""
            menu : ""
        }

        ListElement {
            caption : "search"
            icon : "search.png"
            menu : ""
        }
        ListElement {
            caption : "routes"
            icon : "route.png"
            menu : ""
        }
        ListElement {
            caption : "POI"
            icon : "poi.png"
            menu : ""
        }
        ListElement {
            caption : "info"
            icon : "info.png"
            menu : ""
        }
        ListElement {
            caption : "mode"
            icon : "mode.png"
            menu : ""
        }
        ListElement {
            caption : "options"
            icon : "options.png"
            menu : ""
        }
    }

    // main flickable with icon grid
    GridView {
        anchors.fill : parent
        anchors.topMargin : iconGP.iconMargin/2.0
        //anchors.margins : iconGP.iconMargin
        cellHeight : iconGP.iconSize
        cellWidth : iconGP.iconSize

        model : testModel
        delegate : Item {
            width : iconGP.iconSize
            height : iconGP.iconSize
            // background
            Rectangle {
                anchors.horizontalCenter : parent.horizontalCenter
                anchors.margins : iconGP.iconMargin/2.0
                width : iconGP.iconSize-iconGP.iconMargin/2.0
                height : iconGP.iconSize-iconGP.iconMargin/2.0
                // handle place-holders
                visible : icon != ""
                // TODO: get color from theme
                color : "#92aaf3"
                radius : 10
                smooth : true

                // icon
                TIcon {
                    anchors.horizontalCenter : parent.horizontalCenter
                    iconName : icon
                    anchors.margins : iconGP.iconMargin
                    width : parent.width-iconGP.iconMargin
                    height : parent.height-iconGP.iconMargin
                }
            }
            // caption
            Label {
                text : caption
                anchors.horizontalCenter : parent.horizontalCenter
                anchors.bottom : parent.bottom
                anchors.bottomMargin : iconGP.iconMargin/1.5
            }
            /*
            Rectangle {
                width : iconGP.iconSize
                height : iconGP.iconSize
                //anchors.fill : parent
                color : "blue"
            }*/
        }
    }

    // main "escape" button
    Button {
        anchors.top : parent.top
        anchors.left : parent.left
        anchors.leftMargin : iconGP.iconMargin/2.0
        anchors.topMargin : iconGP.iconMargin/2.0
        width : iconGP.iconSize-iconGP.iconMargin/2.0
        height : iconGP.iconSize-iconGP.iconMargin/2.0
        iconSource: "image://theme/icon-m-common-previous"
        opacity : 0.55
        onClicked : {
            rWin.pageStack.pop()
        }
    }
}