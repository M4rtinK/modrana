//TIcon.qml

/* an automatically themed icon */
import QtQuick 1.1

Image {
    property string iconName : ""
    // TODO: proper slash,backslash,qUrl handling ?

    // handle place-holders
    source : iconName == "" ? "" : "image://icons/" + modrana.theme + "/" + iconName
    fillMode : Image.PreserveAspectFit
    smooth : true
}