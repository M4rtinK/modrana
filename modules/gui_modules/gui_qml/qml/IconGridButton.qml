import QtQuick 1.1
import com.nokia.meego 1.0

Item {
    id : icgb
    property real margin : 0
    property real iconSize : 100
    property alias iconName : themedIcon.iconName
    property alias color : background.color
    property string text : ""
    signal clicked

    width : iconSize
    height : iconSize
    // background
    Rectangle {
        id : background
        anchors.horizontalCenter : icgb.horizontalCenter
        anchors.margins : icgb.margin/2.0
        width : icgb.iconSize-icgb.margin/2.0
        height : icgb.iconSize-icgb.margin/2.0
        // TODO: get color from theme
        //color : icgb.clicked ? "black" : "#92aaf3"
        color : "#92aaf3"
        radius : 10
        smooth : true

        // icon
        TIcon {
            id: themedIcon
            anchors.horizontalCenter : parent.horizontalCenter
            iconName : icon
            anchors.margins : icgb.margin
            width : parent.width-icgb.margin
            height : parent.height-icgb.margin
        }
    }
    // caption
    Label {
        text : icgb.text
        anchors.horizontalCenter : parent.horizontalCenter
        anchors.bottom : parent.bottom
        anchors.bottomMargin : icgb.margin/1.5
    }
    MouseArea {
        id: mouseArea
        anchors.fill: parent
        onClicked: icgb.clicked()
    }
}