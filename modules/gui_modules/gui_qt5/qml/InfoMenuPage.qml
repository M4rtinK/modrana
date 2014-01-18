import QtQuick 2.0

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


        ListElement {
            caption : "Speed"
            icon : "speedometer.png"
            menu : "SpeedPage"
        }
        */

        ListElement {
            caption : "Location"
            icon : "satellite.png"
            menu : "LocationPage"
        }
        ListElement {
            caption : "About"
            icon : "info.png"
            menu : "AboutPage"
        }
    }
}