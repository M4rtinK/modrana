import QtQuick 2.0
import QtQuick.Controls 1.0
import "style.js" as S

Label {
    id : headerLabel
    property string title : ""
    text : title
    property int headerHeight : height/8.0
    property real backButtonW : headerHeight * 0.8
    property bool _fitsIn : (paintedWidth <= (parent.width-backButtonW+(40 * S.style.m)))
    anchors.verticalCenter : parent.verticalCenter
    x: _fitsIn ? 0 : backButtonW + 24 * S.style.m
    width : _fitsIn ? parent.width : parent.width - backButtonW - 40 * S.style.m
    anchors.right : parent.right
    anchors.topMargin : S.style.main.spacing
    anchors.bottomMargin : S.style.main.spacing
    font.pixelSize : 48 * S.style.m
    textFormat : Text.StyledText
    wrapMode : Text.NoWrap
    horizontalAlignment : _fitsIn ? Text.AlignHCenter : Text.AlignLeft
}