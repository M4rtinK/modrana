import QtQuick 2.0
import UC 1.0

Page {
    id : iconGP
    //signal buttonClicked(string menu)
    property alias model : gridView.model
    property int headerHeight : rWin.platform.needs_back_button ? 0 : 100
    property int hIcons : rWin.inPortrait ? 2 : 4
    property double iconMargin : width/(hIcons*10)
    property double iconSize : (width-2)/hIcons
    property alias isMockup : mockup.visible
    property bool hasBackButton : false
    // search, routes, POI, mode, options, info

    // page background
    Rectangle {
        anchors.fill : parent
        color : rWin.theme.color.page_background
        visible : rWin.platform.needs_page_background
    }

    function getPage(menu) {
        return rWin.getPage(menu)
    }

    // main flickable with icon grid
    GridView {
        id : gridView
        anchors.fill : parent
        anchors.topMargin : iconGP.iconMargin/4.0 + iconGP.headerHeight
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
            text : qsTranslate("IconGridPage", caption)
            iconSize : iconGP.iconSize
            margin : iconGP.iconMargin
            onClicked : {
                //send the  button clicked signal
                //iconGP.buttonClicked.send(menu)
                rWin.pushPageInstance(iconGP.getPage(menu))
            }
        }

        //insert the back arrow
        Component.onCompleted: {
            if (rWin.showBackButton && !iconGP.hasBackButton) {
                iconGP.model.insert(0, {"caption": "", "icon":"", "menu":""})
                iconGP.hasBackButton = true
            }
        }

        Connections {
            target : rWin
            onShowBackButtonChanged : {
                if (rWin.showBackButton && !iconGP.hasBackButton) {
                    // add back button
                    iconGP.model.insert(0, {"caption": "", "icon":"", "menu":""})
                    iconGP.hasBackButton = true
                }
                if (!rWin.showBackButton && iconGP.hasBackButton) {
                    // remove the back buttons
                    iconGP.model.remove(0)
                    iconGP.hasBackButton = false
                }

            }
        }
    }

    // main "escape" button

    IconGridButton {
        iconSize : iconGP.iconSize
        margin : iconGP.iconMargin
        anchors.top : gridView.top
        anchors.left : parent.left
        iconName : "left_thin.svg"
        text : "back"
        opacity : gridView.atYBeginning ? 1.0 : 0.55
        visible : rWin.showBackButton
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
    MouseArea {
        anchors.fill : parent
        acceptedButtons: Qt.BackButton
        onClicked: {
            rWin.pageStack.pop(undefined, !rWin.animate)
        }
        onPressAndHold : {
            rWin.pageStack.pop(null, !rWin.animate)
        }
    }
}