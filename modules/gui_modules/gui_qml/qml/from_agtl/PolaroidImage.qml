import QtQuick 1.1
import com.nokia.meego 1.0
import "uiconstants.js" as UI

Rectangle {
    color: "white"
    border.width: 2
    border.color: "#c0c0c0"
    property alias source: image.source
    property alias text: label.text
    property int targetZ: 2
    property int maxWidth: 1000
    property int maxHeight: 1000
    property int borderWidth: 16
    z: targetZ
    Image {
        id: image
        y: borderWidth - (height - paintedHeight)/2
        x: borderWidth
        smooth: true
        z: targetZ + 1
        width: Math.min(sourceSize.width, maxWidth - 2 * borderWidth)
        height: Math.min(sourceSize.height, maxHeight - 2*borderWidth + label.height)
        fillMode: Image.PreserveAspectFit
    }
    smooth: true
    
    Label {
        id: label
        wrapMode: Text.Wrap
        anchors.left: image.left
        anchors.right: image.right
        y: borderWidth + image.paintedHeight + borderWidth
        z: targetZ + 1
        height: (text != "") ? paintedHeight : -borderWidth
    }
    
    height: borderWidth + image.paintedHeight + 2 * borderWidth + label.height
    width: image.width + 2*borderWidth
}

