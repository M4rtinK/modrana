//MTextButton.qml
// A simple button with an icon in the middle.

import QtQuick 2.0
import UC 1.0

MThemedButton {
    id : mtb
    width : tbLabel.contentWidth + 2 * mtb.margin
    height : tbLabel.contentHeight + 2 * mtb.margin
    property alias text : tbLabel.text
    property alias fontSizeMode : tbLabel.fontSizeMode

    Label {
        id : tbLabel
        height : parent.height - 2 * mtb.margin
        font.pixelSize: parent.height
        anchors.verticalCenter : parent.verticalCenter
        anchors.horizontalCenter : parent.horizontalCenter
        elide : Text.ElideRight
        fontSizeMode : Text.Fit
        horizontalAlignment : Text.AlignHCenter
    }
}
