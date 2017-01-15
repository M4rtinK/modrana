import QtQuick 2.0
import UC 1.0

Item {
    id : icgb
    property real margin : 0
    property real iconSize : rWin.c.style.button.iconGrid.size
    property alias iconName : themedIcon.iconName
    property color normalColor : rWin.theme.color.main_fill
    property color toggledColor : rWin.theme.color.icon_grid_toggled
    property alias sensitive : mouseArea.enabled
    property string text : ""
    signal clicked
    signal pressAndHold

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
        radius : rWin.c.style.button.iconGrid.radius
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
        Label {
            smooth : true
            id : iconLabel
            text : icgb.text
            color : rWin.theme.color.icon_button_text
            font.pixelSize : rWin.inPortrait ? rWin.c.style.button.iconGrid.textSizePortrait : rWin.c.style.button.iconGrid.textSizeLandscape
            anchors.horizontalCenter : parent.horizontalCenter
            anchors.bottom : parent.bottom
            anchors.bottomMargin : icgb.margin/2
            property int desiredWidth : background.width-icgb.margin/2
            scale: paintedWidth > desiredWidth ? (desiredWidth / paintedWidth) : 1
            //TODO: find out why the scaled text looks kinda blurry
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
        onPressAndHold : {
            icgb.pressAndHold()
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
             ColorAnimation { target: background; duration: 100*rWin.animate }
             NumberAnimation { properties : "scale"; easing.type : Easing.InOutQuad; duration : 100*rWin.animate }
         },
         Transition {
             from: "RELEASED"
             to: "PRESSED"
             ColorAnimation { target: background; duration: 100*rWin.animate }
             NumberAnimation { properties : "scale"; easing.type : Easing.InOutQuad; duration : 100*rWin.animate }
         }
     ]
}