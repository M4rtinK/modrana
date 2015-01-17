import QtQuick 2.0
import UC 1.0
import "modrana_components"

IconGridPage {
    id : trackMenuPage

    function getPage(menu){
        return Qt.createComponent("Tracks" + menu + ".qml")
    }

    model : ListModel {
        id : testModel
        ListElement {
            caption : "Record"
            icon : "tracklogs.png"
            menu : "RecordPage"
        }
    }
}