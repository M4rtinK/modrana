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
    property alias content: contentField.children
    property alias headerText: headerLabel.text
    property int headerHeight : rWin.inPortrait ? height/7.0 : height/6.0
    Rectangle {
        id : header
        color : "darkgrey"
        anchors.top : parent.top
        anchors.left : parent.left
        anchors.right : parent.right
        height : headerHeight
        Button {
            id : backButton
            width : parent.height * 0.8
            height : parent.height * 0.8
            anchors.top : parent.top
            anchors.left : parent.left
            anchors.topMargin : 8
            anchors.leftMargin : 16
            iconSource : "image://icons/"+ rWin.theme +"/back_small.png"
            onClicked : {
                rWin.pageStack.pop()
            }
        }
        Text {
            id : headerLabel
            property bool _fitsIn : (paintedWidth <= (parent.width-backButton.width+40))
            //width : _fitsIn ? (parent.width - 32) : (parent.width-backButton.width+40)
            //width : 100
            anchors.verticalCenter : parent.verticalCenter
            anchors.left : _fitsIn ? parent.left : backButton.right
            anchors.right : parent.right
            anchors.leftMargin : 24
            anchors.rightMargin : 16
            anchors.topMargin : 8
            anchors.bottomMargin : 8
            //font.pixelSize : headerHeight - 32
            font.pixelSize : 48
            wrapMode : Text.NoWrap
            horizontalAlignment : _fitsIn ? Text.AlignHCenter : Text.AlignLeft


        }
    }
    Rectangle {
        id : contentField
        anchors.top : header.bottom
        anchors.bottom : parent.bottom
        anchors.left : parent.left
        anchors.right : parent.right
    }

}
