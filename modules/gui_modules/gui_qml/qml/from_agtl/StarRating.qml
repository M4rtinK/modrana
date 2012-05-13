import QtQuick 1.1
import "uiconstants.js" as UI
import com.nokia.meego 1.0

Item {
    property real rating: 0
    property real maxrating: 5
    property alias text: title.text
    Label {
        id: title
        font.pixelSize: 20
        y: 0
        color: UI.COLOR_INFOLABEL
        font.weight: Font.Bold
    }
    Image {
        id: marked
        source: "image://theme/icon-m-toolbar-favorite-mark" + (theme.inverted ? "-white" : "")
        fillMode: Image.TileHorizontally
        width: (rating)*sourceSize.width
        anchors.left: parent.left
        y: 26
    }
    Image {
        id: unmarked
        source: "image://theme/icon-m-toolbar-favorite-unmark" + (theme.inverted ? "-white" : "")
        fillMode: Image.TileHorizontally
        width: (maxrating - rating)*sourceSize.width
        anchors.left: marked.right
        y: 26
        mirror: true
    }
    height: marked.height + 26
    anchors.topMargin: 16
    width: maxrating * marked.sourceSize.width
}
