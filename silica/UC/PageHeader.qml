import QtQuick 2.0
import Sailfish.Silica 1.0

PageHeader {
    id : pageHeader
    // NOTE: The color, headerHeight and titlePixelSize
    //       properties actually don't have effect and
    //       are provided for compatibility with the
    //       Controls backed PageHeader where all these
    //       properties *are* effective.
    property color color
    property int headerHeight
    property int titlePixelSize
    property alias menu : gridView.children

    SilicaGridView {
        id : gridView
        anchors.fill : parent
    }
}