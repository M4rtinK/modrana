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
            caption : "Address"
            icon : "signpost.png"
            menu : "Place"
        }
        ListElement {
            caption : "Wikipedia"
            icon : "wikipedia.png"
            menu : "Wikipedia"
        }
        ListElement {
            caption : "Local"
            icon : "local_search.png"
            menu : "Local"
        }
    }
}