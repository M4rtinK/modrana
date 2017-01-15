import QtQuick 2.0
import UC 1.0
import "modrana_components"

BasePage {
    id: aboutPage
    headerText : "modRana " + rWin.platform.modRanaVersion

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
        Image {
            width : 120 * rWin.c.style.m
            height : 120 * rWin.c.style.m
            // If sourceSize is not set an SVG looks blurry - WTF QML ?? :P
            sourceSize.width: parent.width
            sourceSize.height: parent.height
            id : aboutModRanaIcon
            anchors.horizontalCenter : parent.horizontalCenter
            smooth : true

            // TODO: use the Python image provider once Sailfish OS
            //       has PyOtherSide 1.5, which contains a fix for
            //       the broken SVG rendering in older versions
            property string modRanaIconPath : if (rWin.qrc) {
                "qrc:/themes/" + rWin.theme.id +"/modrana.svg"
            } else {
                "file://" + rWin.platform.themesFolderPath + "/" + rWin.theme.id +"/modrana.svg"
            }
            source : modRanaIconPath
            onSourceChanged  : {
                rWin.log.debug("ICON SOURCE: " + source)
            }
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
            wrapMode : Text.WordWrap
            onLinkActivated : {
                rWin.log.info('about text link clicked: ' + link)
                //rWin.notify("Opening:<br><b>"+link+"</b>", 5000)
                Qt.openUrlExternally(link)
            }
        }
    }
}