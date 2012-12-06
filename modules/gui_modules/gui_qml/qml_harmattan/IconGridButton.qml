import QtQuick 1.1
import com.nokia.meego 1.0


Item {
    id : icgb
    property real margin : 0
    property real iconSize : 100
    property alias iconName : themedIcon.iconName
    property color normalColor : "#92aaf3"
    property color toggledColor : "#c6d1f3"
    property alias sensitive : mouseArea.enabled
    property string text : ""
    signal clicked

    //scale : mouseArea.pressed ? 0.9 : 1.0

    width : iconSize
    height : iconSize

    state: "RELEASED"

    // background
    Rectangle {
        id : background
        anchors.horizontalCenter : icgb.horizontalCenter
        anchors.margins : icgb.margin/2.0
        width : icgb.iconSize-icgb.margin/2.0
        height : icgb.iconSize-icgb.margin/2.0
        // TODO: get color from theme
        // TODO: slightly darker (themable ?) pressed color ?
        //property real darking : mouseArea.pressed ? 1.5 : 1.0
        //color : Qt.darker("#92aaf3", darking)
        radius : 10
        smooth : true
        // icon
        TIcon {
            id: themedIcon
            anchors.horizontalCenter : parent.horizontalCenter
            anchors.top : parent.top
            anchors.bottom : iconLabel.top
            iconName : icon
            anchors.topMargin : icgb.margin
            anchors.bottomMargin : icgb.margin/2.0
            width : parent.width-icgb.margin*1.5
            height : parent.height-icgb.margin*1.5
        }
        // caption
        Text {
            smooth : true
            id : iconLabel
            text : icgb.text
            font.pixelSize : rWin.inPortrait ? 42 : 36
            anchors.horizontalCenter : parent.horizontalCenter
            anchors.bottom : parent.bottom
            anchors.bottomMargin : icgb.margin/2
        }
    }
    MouseArea {
        id: mouseArea
        anchors.fill: parent
        onClicked: icgb.clicked()
        //TODO: investigate onPressed transitions
        // e.q. precludes consistent back button behaviour
        //onPressed: icgb.clicked()
        onPressedChanged: {
            pressed ? icgb.state = "PRESSED" : icgb.state = "RELEASED"
        }
        //onReleased: icgb.state = "RELEASED"
    }

    // pressed/released animation
    states: [
         State {
             name: "PRESSED"
             PropertyChanges { target: background; color: toggledColor; scale : 0.9}
             PropertyChanges { target: iconLabel; font.bold : true}
         },
         State {
             name: "RELEASED"
             PropertyChanges { target: background; color: normalColor; scale : 1.0}
             PropertyChanges { target: iconLabel; font.bold : false}
         }
     ]

     transitions: [
         Transition {
             from: "PRESSED"
             to: "RELEASED"
             ColorAnimation { target: background; duration: 100 }
             NumberAnimation { properties : "scale"; easing.type : Easing.InOutQuad; duration : 100 }
         },
         Transition {
             from: "RELEASED"
             to: "PRESSED"
             ColorAnimation { target: background; duration: 100 }
             NumberAnimation { properties : "scale"; easing.type : Easing.InOutQuad; duration : 100 }
         }
     ]
}