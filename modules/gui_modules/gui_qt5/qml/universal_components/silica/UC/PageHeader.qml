import QtQuick 2.0
import Sailfish.Silica 1.0

PageHeader {
    id : pageHeader
    property color color
    property real headerHeight
    property alias menu : gridView.children

    SilicaGridView {
        id : gridView
        anchors.fill : parent
    }
}