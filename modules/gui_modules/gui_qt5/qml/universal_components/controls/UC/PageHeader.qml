import QtQuick 2.0
import QtQuick.Controls 2.0
import "style.js" as S

Label {
    id : headerLabel
    property string title : ""
    text : title
    property int titlePixelSize : 48 * S.style.m
    property int headerHeight : height/8.0
    property real backButtonW : menu ? headerHeight * 0.8 : headerHeight * 0.8 * 2
    property bool _fitsIn : (paintedWidth <= (parent.width-backButtonW+(40 * S.style.m)))
    anchors.verticalCenter : parent.verticalCenter
    x: _fitsIn ? 0 : backButtonW + 24 * S.style.m
    width : _fitsIn ? parent.width : parent.width - backButtonW - 40 * S.style.m
    anchors.right : parent.right
    anchors.topMargin : S.style.main.spacing
    anchors.bottomMargin : S.style.main.spacing
    font.pixelSize : titlePixelSize
    textFormat : Text.StyledText
    wrapMode : Text.NoWrap
    horizontalAlignment : _fitsIn ? Text.AlignHCenter : Text.AlignLeft
    property var menu : null
    property bool menuButtonEnabled : true
    signal _openMenu
    Button {
        visible : menuButtonEnabled && headerLabel.menu
        anchors.right : parent.right
        anchors.rightMargin : 8 * S.style.m
        anchors.verticalCenter : parent.verticalCenter
        width : backButtonW
        height : backButtonW
        Image {
            smooth : true
            source : "menu.svg"
            anchors.verticalCenter : parent.verticalCenter
            anchors.horizontalCenter : parent.horizontalCenter
            width : backButtonW * 0.6
            height : backButtonW * 0.6
        }
        onClicked : {
            if (headerLabel.menu) {
                headerLabel.menu.popup()
            }
        }
    }
}