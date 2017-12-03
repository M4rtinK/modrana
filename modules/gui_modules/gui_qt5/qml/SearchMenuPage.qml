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
            icon : "signpost.png"
            menu : "Address"
        }
        ListElement {
            caption : QT_TRANSLATE_NOOP("IconGridPage", "Wikipedia")
            icon : "wikipedia.png"
            menu : "Wikipedia"
        }
        ListElement {
            caption : QT_TRANSLATE_NOOP("IconGridPage", "Local")
            icon : "local_search.png"
            menu : "Local"
        }
    }
}