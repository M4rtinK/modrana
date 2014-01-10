import QtQuick 2.0
import UC 1.0

Page {
    id : iconGP
    //signal buttonClicked(string menu)
    property alias model : gridView.model
    property int hIcons : rWin.inPortrait ? 2 : 4
    property double iconMargin : width/(hIcons*10)
    property double iconSize : (width-2)/hIcons
    property alias isMockup : mockup.visible
    // search, routes, POI, mode, options, info

    // page background
    Rectangle {
        anchors.fill : parent
        color : rWin.theme.color.page_background
        visible : rWin.platform.needsPageBackground
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
                //send the  button clicked signal
                //iconGP.buttonClicked.send(menu)
                var targetPage = iconGP.getPage(menu)
                if (targetPage) {
                    // go to the page
                    rWin.pageStack.push(targetPage, undefined, !rWin.animate)
                }
            }
        }
        //insert the back arrow
        Component.onCompleted: {
            if (rWin.platform.needsBackButton) {
                model.insert(0, {"caption": "", "icon":"", "menu":""})
            }
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
        visible : rWin.platform.needsBackButton
        onClicked : {
            rWin.pageStack.pop(undefined,!rWin.animate)
        }
        onPressAndHold : {
            rWin.pageStack.pop(null,!rWin.animate)
        }
    }

    Rectangle {
        anchors.verticalCenter : parent.verticalCenter
        anchors.horizontalCenter : parent.horizontalCenter
        id : mockup
        visible : false
        opacity : 0.7
        color: "grey"
        Text {
            anchors.verticalCenter : parent.verticalCenter
            anchors.horizontalCenter : parent.horizontalCenter
            font.pixelSize : 64 * rWin.c.style.m
            text : "MOCKUP"
            color:"white"
        }
    }
}