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

    Rectangle {
        id : header
        color : grey
        anchors.top : parent.top
        anchors.left : parent.left
        anchors.right : parent.right
        height : parent.height/5
        Button {
            width : parent.height * 0.8
            height : parent.height * 0.8
            anchors.top : parent.top
            anchors.left : parent.left
            anchors.topMargin : 16
            anchors.leftMargin : 16
            iconSource : "image://icons/"+ rWin.theme +"/left_thin.png"
            //text : "back"
            onClicked : {
                rWin.pageStack.pop()
            }
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
