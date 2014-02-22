import QtQuick 2.0
import UC 1.0

BasePage {
    id: aboutPage
    headerText : "modRana"
    bottomPadding : rWin.c.style.main.spacingBig*2

    // asynchronously assign properties

    property string payPalUrl : rWin.dcall(
    "modrana.gui.modules.info.getPayPalUrl", [], "", function(v){payPalUrl=v})

    property string flattrUrl : rWin.dcall(
    "modrana.gui.modules.info.getFlattrUrl", [], "", function(v){flattrUrl=v})

    property string bitcoinAddress : rWin.dcall(
    "modrana.gui.modules.info.getBitcoinAddress", [], "", function(v){bitcoinAddress=v})

    property string aboutText : rWin.dcall(
    "modrana.gui.modules.info.getAboutText", [], "", function(v){aboutText=v})

    content {
        Label {
            anchors.top : parent.top
            anchors.topMargin : rWin.c.style.main.spacingBig
            id : aboutTitle
            anchors.horizontalCenter : parent.horizontalCenter
            text: "<h4>version: " + rWin.platform.modRanaVersion + "</h4>"
        }
        Image {
            id : aboutModRanaIcon
            anchors.horizontalCenter : parent.horizontalCenter
            anchors.topMargin : rWin.c.style.main.spacingBig
            anchors.top : aboutTitle.bottom
            source : "image://python/icon/" + rWin.theme.id +"/modrana.svg"
        }

        Label {
            id : donateLabel
            anchors.horizontalCenter : parent.horizontalCenter
            anchors.top : aboutModRanaIcon.bottom
            anchors.topMargin : rWin.c.style.main.spacingBig
            text : "<h3>Dou you like modRana ? <b>Donate !</b></h3>"
        }

        Row {
            id : ppFlattrRow
            anchors.top : donateLabel.bottom
            anchors.horizontalCenter : parent.horizontalCenter
            anchors.topMargin : rWin.c.style.main.spacingBig*2
            spacing : rWin.c.style.main.spacingBig*2
            PayPalButton {
                id : ppButton
                //anchors.top : donateLabel.bottom
                anchors.verticalCenter : parent.verticalCenter
                //anchors.topMargin : rWin.c.style.main.spacingBig*2
                url : aboutPage.payPalUrl
            }

            FlattrButton {
                id : flattrButton
                //anchors.top : ppButton.bottom
                anchors.verticalCenter : parent.verticalCenter
                //anchors.topMargin : 32
                url : aboutPage.flattrUrl
            }
        }
        BitcoinButton {
            id : bitcoinButton
            anchors.top : ppFlattrRow.bottom
            anchors.topMargin : rWin.c.style.main.spacingBig*2
            anchors.horizontalCenter : parent.horizontalCenter
            url : aboutPage.bitcoinAddress
        }

        Label {
            id : contactInfo
            anchors.top : bitcoinButton.bottom
            anchors.topMargin : rWin.c.style.main.spacingBig*2
            height : paintedHeight + rWin.c.style.main.spacingBig*2 - 1
            anchors.left : parent.left
            anchors.leftMargin : rWin.c.style.main.spacingBig
            anchors.right : parent.right
            anchors.rightMargin : rWin.c.style.main.spacingBig
            text: aboutPage.aboutText
            onTextChanged : console.log(text)
            wrapMode : Text.WordWrap
            onLinkActivated : {
                console.log('about text link clicked: ' + link)
                //rWin.notify("Opening:<br><b>"+link+"</b>", 5000)
                Qt.openUrlExternally(link)
            }
        }
    }
}