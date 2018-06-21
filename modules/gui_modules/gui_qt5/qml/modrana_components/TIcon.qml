//TIcon.qml
// an automatically themed icon

import QtQuick 2.0

Image {
    property string iconName : ""
    // TODO: proper slash,backslash,qUrl handling ?

    // handle place-holders
    sourceSize.width : width
    sourceSize.height : height
    source : iconName == "" ? "" : "image://python/icon/" + rWin.theme.id + "/" + iconName
    fillMode : Image.PreserveAspectFit
    smooth : true
    asynchronous : true
}