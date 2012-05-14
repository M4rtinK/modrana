import QtQuick 1.1
import com.nokia.meego 1.0

BasePage {
    id: aboutPage
    headerText : "modRana"
    bottomPadding : 32
    content {
        Label {
            anchors.top : parent.top
            anchors.topMargin : 32
            id : aboutTitle
            anchors.horizontalCenter : parent.horizontalCenter
            text: "<h4>version: " + platform.modRanaVersion() + "</h4>"
        }
        Image {
            id : aboutModRanaIcon
            anchors.horizontalCenter : parent.horizontalCenter
            anchors.topMargin : 32
            anchors.top : aboutTitle.bottom
            source : "image://icons/"+ rWin.theme +"/modrana.svg"
        }
        Button {
            id : donateButton
            text : "Donate ?"
            anchors.horizontalCenter : parent.horizontalCenter
            anchors.topMargin : 32
            anchors.top : aboutModRanaIcon.bottom
            onClicked : {
                console.log('donation button clicked')
                Qt.openUrlExternally(modules.getS("info", "getPayPalUrl"))
            }
        }
        Label {
            id : contactInfo
            anchors.top : donateButton.bottom
            anchors.topMargin : 16
            height : paintedHeight + 31
            anchors.horizontalCenter : parent.horizontalCenter
            text: "<style type='text/css'>p { margin-bottom:15px; margin-top:0px; }</style>" + modules.getS("info", "getAboutText")
            wrapMode : Text.WordWrap
            onLinkActivated : {
                console.log('about text link clicked: ' + link)
                rWin.notify("Opening:<br><b>"+link+"</b>", 5000)
                Qt.openUrlExternally(link)
            }
        }


    }
}