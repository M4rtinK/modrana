import QtQuick 1.1
import "./qtc"

import "functions.js" as F
//import "" + F.bar 1.0;
//import "./" + rWin.foo + "/";

/* base page, includes:
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
            x: _fitsIn ? 0 : backButtonWidth + 24
            width : _fitsIn ? headerWidth : headerWidth - backButtonWidth - 40
            anchors.right : parent.right
            anchors.topMargin : 8
            anchors.bottomMargin : 8
            font.pixelSize : 48
            textFormat : Text.StyledText
            color : modrana.theme.color.page_header_text
            wrapMode : Text.NoWrap
            horizontalAlignment : _fitsIn ? Text.AlignHCenter : Text.AlignLeft
        }
    }
}
