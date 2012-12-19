/* an automatically themed icon */
import QtQuick 1.1

Image {
    property string iconName : ""
    // TODO: proper slash,backslash,qUrl handling ?

    // handle place-holders
    source : iconName == "" ? "" : "image://icons/" + rWin.mTheme + "/" + iconName
    fillMode : Image.PreserveAspectFit
    smooth : true
}