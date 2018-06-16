import QtQuick 2.0
import UC 1.0
import "modrana_components"

BasePage {
    id: aboutPage
    headerText : "modRana " + rWin.platform.modRanaVersion

    property string payPalUrl : rWin.startupValues.aboutModrana.pay_pal_url
    property string flattrUrl : rWin.startupValues.aboutModrana.flattr_url
    property string gratipayUrl : rWin.startupValues.aboutModrana.gratipay_url
    property string bitcoinAddress : rWin.startupValues.aboutModrana.bitcoin_address
    property string emailAddress: rWin.startupValues.aboutModrana.email_address
    property string websiteUrl: rWin.startupValues.aboutModrana.website_url
    property string sourceRepositoryUrl: rWin.startupValues.aboutModrana.source_repository_url
    property string discussionUrl: rWin.startupValues.aboutModrana.discussion_url
    property string translationUrl: rWin.startupValues.aboutModrana.translation_url
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
                rWin.log.debug("modRana icon source: " + source)
            }
        }

        Label {
            id : donateLabel
            width : parent.width
            anchors.horizontalCenter : parent.horizontalCenter
            text : qsTr("<h3>Do you like modRana? <b>Donate:</b></h3>")
            horizontalAlignment : Text.AlignHCenter
            wrapMode : Text.WordWrap
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
            id : mainDeveloperLabel
            width : parent.width
            text : "<b>" + qsTr("Main developer") + "</b>: Martin Kolman"
            wrapMode : Text.WordWrap
        }
        Label {
            id : emailLabel
            width : parent.width
            text : '<b>' + qsTr("Email") + '</b>: <a href="mailto:' + aboutPage.emailAddress + '">' + aboutPage.emailAddress + '</a>'
            wrapMode : Text.WordWrap
            onLinkActivated : {
                rWin.log.info('email link clicked: ' + link)
                Qt.openUrlExternally(link)
            }
        }
        Label {
            id : websiteLabel
            width : parent.width
            text : '<b>' + qsTr('Website') + '</b>: <a href="' + aboutPage.websiteUrl + '">' + aboutPage.websiteUrl + '</a>'
            wrapMode : Text.WordWrap
            onLinkActivated : {
                rWin.log.info('website link clicked: ' + link)
                Qt.openUrlExternally(link)
            }
        }
        Label {
            id : sourceCodeLabel
            width : parent.width
            text : '<b>' + qsTr('Source code') + '</b>: <a href="' + aboutPage.sourceRepositoryUrl + '">' + aboutPage.sourceRepositoryUrl + '</a>'
            wrapMode : Text.WordWrap
            onLinkActivated : {
                rWin.log.info('source code link clicked: ' + link)
                Qt.openUrlExternally(link)
            }
        }
        Label {
            id : discussionLabel
            width : parent.width
            text : '<b>' + qsTr('Forum') + '</b>: <a href="' + aboutPage.discussionUrl + '">' + aboutPage.discussionUrl + '</a>'
            wrapMode : Text.WordWrap
            onLinkActivated : {
                rWin.log.info('forum link clicked: ' + link)
                Qt.openUrlExternally(link)
            }
        }
        Label {
            id : translationLabel
            width : parent.width
            text : '<b>' + qsTr('Translation project') + '</b>: <a href="' + aboutPage.translationUrl + '">' + aboutPage.translationUrl + '</a>'
            wrapMode : Text.WordWrap
            onLinkActivated : {
                rWin.log.info('translation link clicked: ' + link)
                Qt.openUrlExternally(link)
            }
        }
    }
}
