import QtQuick 1.1
import com.nokia.meego 1.0
import "uiconstants.js" as UI
import "functions.js" as F
import QtMultimediaKit 1.1

Page {
    orientationLock: PageOrientation.LockLandscape
    Rectangle {
        color: "black"
        anchors.fill: parent
    }
    onStatusChanged: {
        if (status == PageStatus.Inactive && rootWindow.pageStack.depth == 1) {
            //pageCamera.source = "";
        }
    }
    tools: cameraTools


    property int apertureAngle: 70

    function angleToScreenpoint (a) {
        return camera.width * (a/apertureAngle)
    }
    property double angle: compass.azimuth + 90 // in landscape mode, compass is shifted 90 degress
    property real leftDegrees: Math.floor((angle - apertureAngle/2)/10)*10
    property real offsetPixels: angleToScreenpoint(angle - leftDegrees) - camera.width/2

    Camera {
        id: camera
        y: 0
        width: parent.width
        anchors.horizontalCenter: parent.horizontalCenter
        captureResolution: "1152x648"
        focus: visible
        whiteBalanceMode: Camera.WhiteBalanceAuto
        exposureCompensation: -1.0
        state: (status == PageStatus.Active) ? Camera.ActiveState : Camera.LoadedState


        Repeater {
            model: Math.round(apertureAngle/10) + 1
            delegate:
                Text {
                color: "#00ff00"
                text: (index*10 + camera.leftDegrees) % 360
                font.pixelSize: 20
                x: angleToScreenpoint(index * 10) - camera.offsetPixels - width/2
                y: 8
                style: Text.Outline
                styleColor: "black"
            }

        }

        Rectangle {
            border.color: "#000000"
            border.width: 1
            color: "#00ff00"
            height: 15
            width: 4
            x: angleToScreenpoint(apertureAngle/2)
            y: 30
        }

        Text {
            color: "#00ff00"
            font.pixelSize: 40
            property double targetAngle: (gps.targetBearing - angle + apertureAngle/2 + 360) % 360
            property bool outLeft: targetAngle > apertureAngle && (targetAngle + apertureAngle/2) > 180
            property bool outRight: targetAngle > apertureAngle && (targetAngle + apertureAngle/2) <= 180
            x: outLeft ? 8 :
            outRight ? (camera.width - paintedWidth) :
                (angleToScreenpoint(targetAngle) - paintedWidth/2 - 8)
            y: 45
            text: outLeft ? "<" :
            outRight ? ">" : "^"
            id: ti
            style: Text.Outline
            styleColor: "black"
        }

        Text {
            x: ti.outLeft ? 8 :
            ti.outRight ? (camera.width - paintedWidth - 8) :
                (ti.x + ti.width/2 - width/2)
            anchors.top: ti.bottom
            text: F.formatDistance(gps.targetDistance, settings)
            color: "#00ff00"
            font.pixelSize: 32
            style: Text.Outline
            styleColor: "black"
        }
    }
    
    ToolBarLayout {
        id: cameraTools
        visible: true
        ToolIcon {
            iconId: "toolbar-back" + ((! rootWindow.pageStack.depth || rootWindow.pageStack.depth < 2) ? "-dimmed" : "")// + (theme.inverted ? "-white" : "")
            onClicked: {
                if (rootWindow.pageStack.depth > 1) rootWindow.pageStack.pop();
            }

        }
    }

}
