import QtQuick 2.0
import UC 1.0
import "modrana_components"

IconGridPage {
    id : trackMenuPage

    model : ListModel {
        id : testModel
        ListElement {
            caption : QT_TRANSLATE_NOOP("IconGridPage", "Record")
            icon : "log.svg"
            menu : "TracksRecord"
        }
        ListElement {
            caption : QT_TRANSLATE_NOOP("IconGridPage", "List")
            icon : "list_logs.svg"
            menu : "TracksCategoryList"
        }
    }
}