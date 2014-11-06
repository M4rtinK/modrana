import Sailfish.Silica 1.0

IconButton {
    property string iconSource : ""
    property bool checkable : false
    property bool checked : false
    onIconSourceChanged : {
        icon.source = iconSource
    }
}