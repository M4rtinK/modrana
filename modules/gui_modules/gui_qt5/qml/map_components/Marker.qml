import QtQuick 2.0

Rectangle {
    id: marker
    width: 20 * rWin.c.style.m
    height: 20 * rWin.c.style.m
    property var targetPoint
    property var point
    x: targetPoint[0] - width/2
    y: targetPoint[1] - height/2
    border.width: 3 * rWin.c.style.m
    border.color: point.highlight ? "red" : "blue"
    radius: 7 * rWin.c.style.m
}
