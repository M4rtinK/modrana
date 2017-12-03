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

        /*
        ListElement {
            caption : "Compass"
            icon : "compass.png"
            menu : "CompassPage"
        }
        */

        ListElement {
            caption : QT_TRANSLATE_NOOP("IconGridPage", "Speed")
            icon : "speedometer.png"
            menu : "SpeedPage"
        }


        ListElement {
            caption : QT_TRANSLATE_NOOP("IconGridPage", "Location")
            icon : "satellite.png"
            menu : "LocationPage"
        }
        ListElement {
            caption : QT_TRANSLATE_NOOP("IconGridPage", "About")
            icon : "info.png"
            menu : "AboutPage"
        }
    }
}