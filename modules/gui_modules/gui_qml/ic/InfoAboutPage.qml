import QtQuick 1.1
import "./qtc"

BasePage {
    id: aboutPage
    headerText : "modRana"
    bottomPadding : C.style.main.spacingBig*2
    content {
        Label {
            anchors.top : parent.top
            anchors.topMargin : C.style.main.spacingBig
            id : aboutTitle
            anchors.horizontalCenter : parent.horizontalCenter
            text: "<h4>version: " + platform.modRanaVersion() + "</h4>"
        }
        Image {
            id : aboutModRanaIcon
            anchors.horizontalCenter : parent.horizontalCenter
            anchors.topMargin : C.style.main.spacingBig
            anchors.top : aboutTitle.bottom
            source : "image://icons/"+ modrana.theme_id +"/modrana.svg"
        }

        Label {
            id : donateLabel
            anchors.horizontalCenter : parent.horizontalCenter
            anchors.top : aboutModRanaIcon.bottom
            anchors.topMargin : C.style.main.spacingBig
            text : "<h3>Dou you like modRana ? <b>Donate !</b></h3>"
        }

        Row {
            id : ppFlattrRow
            anchors.top : donateLabel.bottom
            anchors.horizontalCenter : parent.horizontalCenter
            anchors.topMargin : C.style.main.spacingBig*2
            spacing : C.style.main.spacingBig*2
            PayPalButton {
                id : ppButton
                //anchors.top : donateLabel.bottom
                anchors.verticalCenter : parent.verticalCenter
                //anchors.topMargin : C.style.main.spacingBig*2
                url : modules.getS("info", "getPayPalUrl")
            }

            FlattrButton {
                id : flattrButton
                //anchors.top : ppButton.bottom
                anchors.verticalCenter : parent.verticalCenter
                //anchors.topMargin : 32
                url : modules.getS("info", "getFlattrUrl")
            }
        }
        BitcoinButton {
            id : bitcoinButton
            anchors.top : ppFlattrRow.bottom
            anchors.topMargin : C.style.main.spacingBig*2
            anchors.horizontalCenter : parent.horizontalCenter
            url : modules.getS("info", "getBitcoinAddress")
        }

        Label {
            id : contactInfo
            anchors.top : bitcoinButton.bottom
            anchors.topMargin : C.style.main.spacingBig*2
            height : paintedHeight + C.style.main.spacingBig*2 - 1
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