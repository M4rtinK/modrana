import QtQuick 2.0
import UC 1.0

Page {
    //color : "blue"
    id : mapPage
    //width : 640
    //height : 480

    //opacity : 0.5


    //property int speedT : rWin.get("voiceVolume", 1234, function(v){speedT = v})
    property int speedT : rWin.get("voiceVolume", 1234, speedT)
    //property int speedT : rWin.get_sync("voiceVolume", 1234)

    Rectangle {
        anchors.top : parent.top
        anchors.left : parent.left
        width : 300
        height : 200
        color : "green"
    }

    Label {
        id : testText
        anchors.top : parent.top
        anchors.topMargin : 100
        anchors.left : parent.left
        anchors.right : parent.right
//        width : parent.height
        height : parent.height
        color : "white"
        text : "Hello World! " + speedT
        font.pixelSize: 22

    }

    Rectangle {
        anchors.top : testText.bottom
        anchors.left : parent.left
        width : 300
        height : 200
        color : "white"
    }

}