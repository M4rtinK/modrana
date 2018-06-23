import QtQuick 2.0
import "modrana_components"

// map, ui, POI, navigation, network, debug

IconGridPage {
    function getPage(menu){
        return Qt.createComponent("Info" + menu + ".qml")
    }

    isMockup: false
    model : ListModel {
        id : testModel
        ListElement {
            caption : QT_TRANSLATE_NOOP("IconGridPage", "Speed")
            icon : "speedometer.svg"
            menu : "SpeedPage"
        }
        ListElement {
            caption : QT_TRANSLATE_NOOP("IconGridPage", "Location")
            icon : "satellite.svg"
            menu : "LocationPage"
        }
        ListElement {
            caption : QT_TRANSLATE_NOOP("IconGridPage", "About")
            icon : "info.svg"
            menu : "AboutPage"
        }
    }
}