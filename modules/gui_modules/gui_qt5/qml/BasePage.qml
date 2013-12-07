import QtQuick 2.0
import UC 1.0

/* base modRana page, includes:
   * a header, with a
    * back button
    * page name
    * optional tools button
 useful for things like track logging menus,
 about menus, compass pages, point pages, etc.
*/

HeaderPage {
    id : searchPage
    property alias headerTextColor : headerLabel.color
    property alias headerText: headerLabel.text
    headerContent {
        Label {
            id : headerLabel
            property bool _fitsIn : (paintedWidth <= (parent.width-backButtonWidth+40))
            anchors.verticalCenter : parent.verticalCenter
            x: _fitsIn ? 0 : backButtonWidth + 24 * rWin.c.style.m
            width : _fitsIn ? headerWidth : headerWidth - backButtonWidth - 40
            anchors.right : parent.right
            anchors.topMargin : rWin.c.style.main.spacing
            anchors.bottomMargin : rWin.c.style.main.spacing
            font.pixelSize : 48 * rWin.c.style.m
            textFormat : Text.StyledText
            color : rWin.theme.color.page_header_text
            wrapMode : Text.NoWrap
            horizontalAlignment : _fitsIn ? Text.AlignHCenter : Text.AlignLeft
        }
    }
}
