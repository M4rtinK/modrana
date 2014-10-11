import QtQuick 2.0
import UC 1.0
import "modrana_components"

BasePage {
    id: aboutPage
    headerText : "modRana"
    bottomPadding : rWin.c.style.main.spacingBig*2

    // asynchronously assign properties

    property string payPalUrl : rWin.dcall(
    "modrana.gui.modules.info.getPayPalUrl", [], "", function(v){payPalUrl=v})

    property string flattrUrl : rWin.dcall(
    "modrana.gui.modules.info.getFlattrUrl", [], "", function(v){flattrUrl=v})

    property string gratipayUrl : rWin.dcall(
    "modrana.gui.modules.info.getGratipayUrl", [], "", function(v){gratipayUrl=v})

    property string bitcoinAddress : rWin.dcall(
    "modrana.gui.modules.info.getBitcoinAddress", [], "", function(v){bitcoinAddress=v})

    property string aboutText : rWin.dcall(
    "modrana.gui.modules.info.getAboutText", [], "", function(v){aboutText=v})

    content : ContentColumn {
        Label {
            id : aboutTitle
            anchors.horizontalCenter : parent.horizontalCenter
            text: "<h4>version: " + rWin.platform.modRanaVersion + "</h4>"
            width : parent.width
            horizontalAlignment : Text.AlignHCenter
            wrapMode : Text.Wrap
        }
        Image {
            id : aboutModRanaIcon
            anchors.horizontalCenter : parent.horizontalCenter
            source : "image://python/icon/" + rWin.theme.id +"/modrana.svg"
        }

        Label {
            id : donateLabel
            anchors.horizontalCenter : parent.horizontalCenter
            text : "<h3>Dou you like modRana ? <b>Donate !</b></h3>"
        }
        Column {
            anchors.horizontalCenter : parent.horizontalCenter
            spacing : rWin.c.style.main.spacingBig * 2
            Row {
                id : ppFlattrRow
                anchors.horizontalCenter : parent.horizontalCenter
                spacing : rWin.c.style.main.spacingBig*2
                PayPalButton {
                    id : ppButton
                    anchors.verticalCenter : parent.verticalCenter
                    url : aboutPage.payPalUrl
                }
                FlattrButton {
                    id : flattrButton
                    anchors.verticalCenter : parent.verticalCenter
                    url : aboutPage.flattrUrl
                }
            }
            Row {
                id : bitcoinGPRow
                anchors.horizontalCenter : parent.horizontalCenter
                spacing : rWin.c.style.main.spacingBig*2
                GratipayButton {
                    id : gpButton
                    anchors.verticalCenter : parent.verticalCenter
                    url : aboutPage.gratipayUrl
                }
                BitcoinButton {
                    id : bitcoinButton
                    anchors.verticalCenter : parent.verticalCenter
                    url : aboutPage.bitcoinAddress
                }
            }
        }

        Label {
            id : contactInfo
            height : paintedHeight + rWin.c.style.main.spacingBig*2 - 1
            width : parent.width
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