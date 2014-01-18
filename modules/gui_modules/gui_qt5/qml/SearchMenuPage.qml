import QtQuick 1.1
import "./qtc"

// map, ui, POI, navigation, network, debug



IconGridPage {
    id : searchMenuPage
    function getPage(menu){
        return Qt.createComponent("Search" + menu + ".qml")
    }
    model : ListModel {
        id : testModel
        ListElement {
            caption : "Address"
            icon : "signpost.png"
            menu : "AddressPage"
        }
    }
}