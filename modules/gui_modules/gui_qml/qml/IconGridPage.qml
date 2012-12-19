import QtQuick 1.1
import "./qtc"

Page {
    property alias model : gridView.model

    id : iconGP
    property int hIcons : rWin.inPortrait ? 2 : 4
    property double iconMargin : width/(hIcons*10)
    property double iconSize : (width-2)/hIcons
    property alias isMockup : mockup.visible
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
            // handle place-holders
            visible : icon != ""
            iconName : icon
            text : caption
            iconSize : iconGP.iconSize
            margin : iconGP.iconMargin
            onClicked : {
                //rWin.pageStack.push(rWin.getPage(menu))
                var targetPage = iconGP.getPage(menu)
                if (targetPage != null) {
                    // go to the page
                    rWin.pageStack.push(targetPage)
                } else {
                    // go back to the map page
                    //rWin.pageStack.clear()
                    //TODO: find out if the stack can overfill
                    rWin.pageStack.push(mapPage)
                }

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
        anchors.topMargin : iconGP.iconMargin/4.0
        iconName : "left_thin.png"
        text : "back"
        opacity : gridView.atYBeginning ? 1.0 : 0.55
        onClicked : {
            rWin.pageStack.pop()
        }
    }

    Rectangle {
        anchors.verticalCenter : parent.verticalCenter
        anchors.horizontalCenter : parent.horizontalCenter
        id : mockup
        visible : false
        opacity : 0.7
        color: "grey"
        Label {
            anchors.verticalCenter : parent.verticalCenter
            anchors.horizontalCenter : parent.horizontalCenter
            font.pixelSize : 64
            text : "MOCKUP"
            color:"white"
        }
    }
}