import QtQuick 1.1
import com.nokia.meego 1.0

BasePage {
    id: aboutPage
    /*
    anchors.fill : parent
    anchors.topMargin : 20
    anchors.bottomMargin : 30
    anchors.leftMargin : 30
    anchors.rightMargin : 30
    */
    headerText : "modRana"
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
        Label {
            id : aboutContactInfo
            anchors.horizontalCenter : parent.horizontalCenter
            //anchors.topMargin : 10
            anchors.top : aboutModRanaIcon.bottom
            //text: "<style type='text/css'>p { margin-bottom:15px; margin-top:0px; }</style>" + repho.getAboutText()

            onLinkActivated : {
                console.log('about text link clicked: ' + link)
                mainView.notify("Opening:<br><b>"+link+"</b>")
                Qt.openUrlExternally(link)
            }
        }
        Button {
            text : "Donate ?"
            anchors.horizontalCenter : parent.horizontalCenter
            anchors.topMargin : 25
            anchors.top : aboutContactInfo.bottom
            onClicked : {
                console.log('donation button clicked')
                Qt.openUrlExternally(platform.getPayPalUrl())
            }
        }
    }
}