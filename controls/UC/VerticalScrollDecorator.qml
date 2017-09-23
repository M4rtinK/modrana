import QtQuick 2.0
import QtQuick.Controls 2.0

// A scroll decorator working in a similar way to the Silica VerticalStrollDecorator,
// but based on the QtQuick Controls 2 Scroll bar (which, like other new QQC2 elements
// really looks to be Silica inspired).
//
// NOTE: This is just scroll decorator. If you want to scroll bar that can be dragged to
//        move the view content use the ScrollBar UC element.

ScrollBar {
    function findFlickable(item) {
        var parentItem = item.parent
        while (parentItem) {
            if (parentItem.maximumFlickVelocity) {
                return parentItem
            }
            parentItem = parentItem.parent
        }
        return null
    }

    id: vbar
    hoverEnabled: true
    active: hovered || pressed || flickable.flickingVertically
    orientation: Qt.Vertical
    size: flickable.height / flickable.contentHeight
    anchors.top: parent.top
    anchors.right: parent.right
    anchors.bottom: parent.bottom
    property Flickable flickable : findFlickable(vbar)





}
