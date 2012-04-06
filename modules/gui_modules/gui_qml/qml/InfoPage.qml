import QtQuick 1.1
import com.nokia.meego 1.0

Page {

    Label {
        anchors.verticalCenter : parent.verticalCenter
        anchors.horizontalCenter : parent.horizontalCenter
        font.pixelSize : 32
        text : "modRana version:<br>" + platform.modRanaVersion()
        color:"black"
    }


    Button {
        width : 150
        height : 150
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