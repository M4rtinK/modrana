import QtQuick 1.1
import com.nokia.meego 1.0


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
    property alias content: contentField.children
    property alias headerText: headerLabel.text
    property int headerHeight : rWin.inPortrait ? height/7.0 : height/5.5
    property int bottomPadding : 0
    ScrollDecorator {
         id: scrolldecorator
         flickableItem: pageFlickable
    }

    Rectangle {
        id : background
        color : "lightgrey"
        anchors.fill : parent
    }

    Flickable {
        id : pageFlickable
        anchors.fill: parent
        contentWidth: parent.width
        contentHeight: (headerHeight + contentField.childrenRect.height + bottomPadding)
        //flickableDirection: Flickable.VerticalFlick
        Rectangle {
            id : header
            color : "#92aaf3"
            anchors.top : parent.top
            anchors.left : parent.left
            anchors.right : parent.right
            height : headerHeight
            Text {
                id : headerLabel
                property bool _fitsIn : (paintedWidth <= (parent.width-backButton.width+40))
                anchors.verticalCenter : parent.verticalCenter
                x: _fitsIn ? 0 : backButton.width + 24
                width : _fitsIn ? header.width : header.width - backButton.width - 40
                anchors.right : parent.right
                anchors.topMargin : 8
                anchors.bottomMargin : 8
                font.pixelSize : 48
                wrapMode : Text.NoWrap
                horizontalAlignment : _fitsIn ? Text.AlignHCenter : Text.AlignLeft
            }
        }
        Rectangle {
            id : contentField
            anchors.top : header.bottom
            //height : childrenRect.height
            anchors.bottom : parent.bottom
            anchors.left : parent.left
            anchors.right : parent.right
        }
    }
    Button {
        id : backButton
        width : headerHeight * 0.8
        height : headerHeight * 0.8
        anchors.top : parent.top
        anchors.left : parent.left
        anchors.topMargin : 8
        anchors.leftMargin : 16
        iconSource : "image://icons/"+ rWin.mTheme +"/back_small.png"
        opacity : pageFlickable.atYBeginning ? 1.0 : 0.55
        onClicked : {
            rWin.pageStack.pop()
        }
    }

}
