import QtQuick 2.0
import QtQuick.Controls 1.0

Label {
    id : headerLabel
    property string title : ""
    text : title
    property real backButtonW : rWin.headerHeight * 0.8
    property bool _fitsIn : (paintedWidth <= (parent.width-backButtonW+(40 * rWin.c.style.m)))
    anchors.verticalCenter : parent.verticalCenter
    x: _fitsIn ? 0 : backButtonW + 24 * rWin.c.style.m
    width : _fitsIn ? parent.width : parent.width - backButtonW - 40 * rWin.c.style.m
    anchors.right : parent.right
    anchors.topMargin : rWin.c.style.main.spacing
    anchors.bottomMargin : rWin.c.style.main.spacing
    font.pixelSize : 48 * rWin.c.style.m
    textFormat : Text.StyledText
    color : rWin.theme.color.page_header_text
    wrapMode : Text.NoWrap
    horizontalAlignment : _fitsIn ? Text.AlignHCenter : Text.AlignLeft
}