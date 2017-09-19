//NavigationOverlay.qml

// Not really a full screen overlay, but stile meant to overlay the top
// of the map screen with slight transparency.

import QtQuick 2.0
import UC 1.0

Rectangle {
    id : nbr
    color : rWin.theme.color.main_fill
    opacity : 0.85
}
