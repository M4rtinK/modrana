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
            caption : QT_TRANSLATE_NOOP("IconGridPage", "Place")
            icon : "signpost.svg"
            menu : "Address"
        }
        ListElement {
            caption : QT_TRANSLATE_NOOP("IconGridPage", "Wikipedia")
            icon : "wikipedia.svg"
            menu : "Wikipedia"
        }
        ListElement {
            caption : QT_TRANSLATE_NOOP("IconGridPage", "Local")
            icon : "local_search.svg"
            menu : "Local"
        }
    }
}