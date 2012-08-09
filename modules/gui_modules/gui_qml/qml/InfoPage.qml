import QtQuick 1.1
import com.nokia.meego 1.0

BasePage {
    id: aboutPage
    headerText : "modRana"
    bottomPadding : 32
    content {
        Label {
            anchors.top : parent.top
            anchors.topMargin : 16
            id : aboutTitle
            anchors.horizontalCenter : parent.horizontalCenter
            text: "<h4>version: " + platform.modRanaVersion() + "</h4>"
        }
        Image {
            id : aboutModRanaIcon
            anchors.horizontalCenter : parent.horizontalCenter
            anchors.topMargin : 16
            anchors.top : aboutTitle.bottom
            source : "image://icons/"+ rWin.mTheme +"/modrana.svg"
        }

        Label {
            id : donateLabel
            anchors.horizontalCenter : parent.horizontalCenter
            anchors.top : aboutModRanaIcon.bottom
            anchors.topMargin : 16
            text : "<h3>Dou you like modRana ? <b>Donate !</b></h3>"
        }

        PayPalButton {
            id : ppButton
            anchors.top : donateLabel.bottom
            anchors.horizontalCenter : parent.horizontalCenter
            anchors.topMargin : 32
            url : modules.getS("info", "getPayPalUrl")
        }

        FlattrButton {
            id : flattrButton
            anchors.top : ppButton.bottom
            anchors.horizontalCenter : parent.horizontalCenter
            anchors.topMargin : 32
            url : modules.getS("info", "getFlattrUrl")
        }
        Label {
            id : contactInfo
            anchors.top : flattrButton.bottom
            anchors.topMargin : 32
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