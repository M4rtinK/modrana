import QtQuick 2.0
import UC 1.0

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