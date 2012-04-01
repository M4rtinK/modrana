import QtQuick 1.1
import com.nokia.meego 1.0

Page {
    property alias model : gridView.model

    id : iconGP
    property int hIcons : rWin.inPortrait ? 2 : 4
    property double iconMargin : width/(hIcons*10)
    property double iconSize : (width-2)/hIcons
    // search, routes, POI, mode, options, info

    // page background
    Rectangle {
        anchors.fill : parent
        color : "black"
    }

    function getPage(menu) {
        return rWin.getPage(menu)
    }

    // main flickable with icon grid
    GridView {
        id : gridView
        anchors.fill : parent
        anchors.topMargin : iconGP.iconMargin/4.0
        //anchors.margins : iconGP.iconMargin
        cellHeight : iconGP.iconSize
        cellWidth : iconGP.iconSize

        // default empty list model
        model : ListModel {
        }


        delegate : IconGridButton {
            //anchors.fill : parent
            // handle place-holders
            visible : icon != ""
            iconName : icon
            text : caption
            iconSize : iconGP.iconSize
            margin : iconGP.iconMargin
            onClicked : {
                //rWin.pageStack.push(rWin.getPage(menu))
                rWin.pageStack.push(iconGP.getPage(menu))
            }
        }
        //insert the back arrow
        Component.onCompleted: {
            model.insert(0, {"caption": "", "icon":"", "menu":""})
        }


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
        iconName : "left_thin.png"
        text : "back"
        //normalColor : "#4973f3"
        //normalColor : "#3d6af3"
        //normalColor : "#3161f3"
        //toggledColor: "#92aaf3"
        opacity : gridView.atYBeginning ? 1.0 : 0.55
        onClicked : {
            rWin.pageStack.pop()
        }
    }
}