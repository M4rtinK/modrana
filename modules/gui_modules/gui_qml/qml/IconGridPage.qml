import QtQuick 1.1
import com.nokia.meego 1.0

Page {
    id : iconGP
    property double iconMargin : width/20.0
    property int hIcons : rWin.inPortrait ? 2 : 4
    property double iconSize : (width-2)/hIcons
    // search, routes, POI, mode, options, info

    // page background
    Rectangle {
        anchors.fill : parent
        color : "black"
    }


    ListModel {
        id : testModel

        ListElement {
            caption : "back"
            icon : "left_arrow_black.png"
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
        anchors.topMargin : iconGP.iconMargin/4.0
        //anchors.margins : iconGP.iconMargin
        cellHeight : iconGP.iconSize
        cellWidth : iconGP.iconSize

        model : testModel
        delegate : IconGridButton {
            //anchors.fill : parent
            // handle place-holders
            visible : icon != ""
            iconName : icon
            text : caption
            iconSize : iconGP.iconSize
            margin : iconGP.iconMargin
        }
        Component.onCompleted: console.log("AASDASDASDASDASDASD")
        //Component.onCompleted: console.log("icon grid " + model)


    }

    // main "escape" button

    IconGridButton {
        iconSize : iconGP.iconSize
        margin : iconGP.iconMargin
        anchors.top : parent.top
        anchors.left : parent.left
        //anchors.leftMargin : iconGP.iconMargin/12.0
        anchors.topMargin : iconGP.iconMargin/4.0
        //width : iconGP.iconSize-iconGP.iconMargin/2.0
        //height : iconGP.iconSize-iconGP.iconMargin/2.0
        iconName : "left_arrow_black.png"
        text : "back"
        color : "blue"
        opacity : 0.55
        onClicked : {
            rWin.pageStack.pop()
        }
    }
}