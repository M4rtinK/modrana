//TwoOptionsPage.qml

import QtQuick 2.0
import UC 1.0

BasePage {
    id : twoOptionPage
    headerText: ""
    property alias text : mainLabel.text
    property alias firstButtonText : firstButton.text
    property alias firstButtonNormalColor : firstButton.normalColor
    property alias firstButtonHighlightedColor : firstButton.highlightedColor
    signal firstButtonClicked
    property alias secondButtonText : secondButton.text
    property alias secondButtonNormalColor : secondButton.normalColor
    property alias secondButtonHighlightedColor : secondButton.highlightedColor
    signal secondButtonClicked
    content : ContentColumn {
        anchors.topMargin : rWin.c.style.main.spacing * 2
        spacing : rWin.isDesktop ? rWin.c.style.main.spacing * 2 :
                                   rWin.c.style.main.spacing * 7
        id: textAndOptions
        Label {
            id : mainLabel
            width : parent.width
            wrapMode : Text.WordWrap
            horizontalAlignment : Text.AlignHCenter
        }
        SmartGrid {
            spacing : rWin.c.style.main.spacing * 2
            TextButton {
                id : firstButton
                width : parent.cellWidth
                text: ""
                normalColor : "grey"
                highlightedColor : rWin.theme.color.icon_button_toggled
                onClicked: {
                    firstButtonClicked()
                }
            }
            TextButton {
                id : secondButton
                width : parent.cellWidth
                text: ""
                normalColor : "grey"
                highlightedColor : rWin.theme.color.icon_button_toggled
                onClicked: {
                    secondButtonClicked()
                }
            }
        }
    }
}