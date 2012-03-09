/* an automatically themed icon */
import QtQuick 1.1
import com.nokia.meego 1.0

Image {
    property string iconName : ""
    // TODO: proper slash,backslash,qUrl handling ?

    // handle place-holders
    source : iconName == "" ? "" : "image://icons/" + rWin.theme + "/" + iconName
    fillMode : Image.PreserveAspectFit
    smooth : true
}