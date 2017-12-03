import QtQuick 2.0
import UC 1.0
import "modrana_components"

IconGridPage {
    id : searchMenuPage
    function getPage(menu){
        return rWin.getPage("Search" + menu)
    }
    model : ListModel {
        id : testModel
        ListElement {
            caption : QT_TR_NOOP("Place")
            icon : "signpost.png"
            menu : "Address"
        }
        ListElement {
            caption : QT_TR_NOOP("Wikipedia")
            icon : "wikipedia.png"
            menu : "Wikipedia"
        }
        ListElement {
            caption : QT_TR_NOOP("Local")
            icon : "local_search.png"
            menu : "Local"
        }
    }
}