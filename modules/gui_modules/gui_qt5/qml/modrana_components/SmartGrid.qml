// SmartGrid.qml
// Smart Grid is a smart Grid element that shows one column in portrait
// and two columns in landscape.

import QtQuick 2.0

Grid {
    id : smartGrid
    spacing : rWin.c.style.main.spacing
    width : rWin.inPortrait ? parent.width : parent.width - smartGrid.spacing
    property real cellWidth : width/columns
    // 2 columns in landscape, 1 in portrait
    columns : rWin.inPortrait ? 1 : 2
    rowSpacing : rWin.inPortrait ? smartGrid.spacing : 0
    columnSpacing : rWin.inPortrait ? 0 : smartGrid.spacing
}