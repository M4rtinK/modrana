import QtQuick 1.1
import "./qtc"

import "functions.js" as F
//import "" + F.bar 1.0;
//import "./" + rWin.foo + "/";

/* base page, includes:
   * a header, with a
    * back button
    * page name
    * optional tools button
 useful for things like track logging menus,
 about menus, compass pages, point pages, etc.
*/

Page {
    anchors.fill : parent
    property alias content : contentField.children
    property alias headerContent : hContent.children
    property alias headerWidth : header.width
    property alias backButtonWidth : backButton.width
    property int headerHeight : rWin.inPortrait ? height/7.0 : height/5.5
    property int bottomPadding : 0
    property real availableHeight : parent.height - bottomPadding - headerHeight
    property alias isFlickable :  pageFlickable.interactive
    ScrollDecorator {
         id: scrolldecorator
         flickableItem: pageFlickable
    }

    /*
    Rectangle {
        id : background
        color : "white"
        anchors.fill : parent
        //visible : false
    }
    */

    Flickable {
        id : pageFlickable
        anchors.fill: parent
        contentWidth: parent.width
        contentHeight: (headerHeight + contentField.childrenRect.height + bottomPadding)
        //flickableDirection: Flickable.VerticalFlick
        Item {
            id : contentField
            anchors.top : header.bottom
            //height : childrenRect.height
            anchors.bottom : parent.bottom
            anchors.left : parent.left
            anchors.right : parent.right
        }
        Rectangle {
            id : header
            color : modrana.theme.color.main_fill
            anchors.top : parent.top
            anchors.left : parent.left
            anchors.right : parent.right
            height : headerHeight
            Item {
                id : hContent
                width : headerWidth - backButton.width - 16
                anchors.right : parent.right
                anchors.top : parent.top
                height : headerHeight
            }
        }
    }
    IconButton {
        id : backButton
        width : headerHeight * 0.8
        height : headerHeight * 0.8
        anchors.top : parent.top
        anchors.left : parent.left
        anchors.topMargin : 8
        anchors.leftMargin : 16
        iconName : "left_thin.png"
        //iconSource : "image://icons/"+ modrana.theme_id +"/back_small.png"
        opacity : pageFlickable.atYBeginning ? 1.0 : 0.55
        onClicked : {
            rWin.pageStack.pop(undefined, !rWin.animate)
        }

        onPressAndHold : {
            rWin.pageStack.pop(null, !rWin.animate)
        }
    }
}
