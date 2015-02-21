import QtQuick 2.0
import UC 1.0
import "modrana_components"

IconGridPage {
    id : trackMenuPage

    model : ListModel {
        id : testModel
        ListElement {
            caption : "Record"
            icon : "log.png"
            menu : "TracksRecord"
        }
    }
}