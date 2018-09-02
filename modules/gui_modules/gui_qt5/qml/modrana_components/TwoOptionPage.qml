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
        id: textAndOptions
        Label {
            id : mainLabel
            width : parent.width
            wrapMode : Text.WordWrap

        }
        SmartGrid {
            width : parent.width - rWin.c.style.main.spacing
            TextButton {
                id : firstButton
                width : parent.cellWidth
                text: ""
                onClicked: {
                    firstButtonClicked()
                }
            }
            TextButton {
                id : secondButton
                width : parent.cellWidth
                text: ""
                onClicked: {
                    secondButtonClicked()
                }
            }
        }
    }
}