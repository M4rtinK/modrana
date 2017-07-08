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
    id : headerPage
    property alias headerTextColor : headerLabel.color
    property alias headerText : headerLabel.title
    property alias headerMenu : headerLabel.menu
    headerContent : PageHeader {
        id : headerLabel
        // override the default header height with a dynamic
        // (depends on back button being shown) modRana specific value
        headerHeight : rWin.headerHeight
        color : rWin.theme.color.page_header_text
        titlePixelSize : rWin.isDesktop ? 32 * rWin.c.style.m : 48 * rWin.c.style.m
        visible : headerPage.headerVisible
        menuButtonEnabled : false
    }

    Button {
        visible : headerMenu && rWin.platform.needs_back_button
        // so likely also needs menu button (but we should still split it in the future)
        anchors.top : parent.top
        anchors.topMargin : (headerHeight - height) / 2.0
        anchors.right : parent.right
        anchors.rightMargin : rWin.c.style.main.spacingBig
        width : headerHeight * 0.8
        height : headerHeight * 0.8
        Image {
            smooth : true
            source : "menu.svg"
            anchors.verticalCenter : parent.verticalCenter
            anchors.horizontalCenter : parent.horizontalCenter
            width : headerHeight * 0.6
            height : headerHeight * 0.6
        }
        onClicked : {
            if (headerMenu) {
                headerMenu.popup()
            }
        }
    }

}
