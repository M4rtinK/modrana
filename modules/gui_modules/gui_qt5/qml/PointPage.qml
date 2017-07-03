//PointPage.qml

import QtQuick 2.0
import UC 1.0
import "modrana_components"

BasePage {
    id: pointPage
    headerText : point.name
    property var point

    content : ContentColumn {
        Label {
            text : point.description
            width : parent.width
            wrapMode : Text.WordWrap
        }
   }
}
