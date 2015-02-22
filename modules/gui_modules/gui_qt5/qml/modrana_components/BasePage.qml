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
    property alias headerText: headerLabel.title
    headerContent : PageHeader {
        id : headerLabel
        // override the default header height with a dynamic
        // (depends on back button being shown) modRana specific value
        headerHeight : rWin.headerHeight
        color : rWin.theme.color.page_header_text
    }
}
