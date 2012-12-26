import QtQuick 1.1

// map, ui, POI, navigation, network, debug


IconGridPage {

    InfoAboutPage {
        id : aboutPage
    }

    function getPage(menu){
        if (menu == "aboutPage") {
            return aboutPage
        } else if (menu == "speedPage") {
            return Qt.createComponent("InfoSpeedPage.qml")
        } else if (menu == "locationPage") {
            return Qt.createComponent("InfoLocationPage.qml")
        }
    }

    isMockup: false
    model : ListModel {
        id : testModel

        ListElement {
            caption : "Compass"
            icon : "compass.png"
            menu : ""
        }

        ListElement {
            caption : "Speed"
            icon : "speedometer.png"
            menu : "speedPage"
        }
        ListElement {
            caption : "Location"
            icon : "satellite.png"
            menu : "locationPage"
        }
        ListElement {
            caption : "About"
            icon : "info.png"
            menu : "aboutPage"
        }
    }
    /*
    Loader {
        id: infoPage1
        source: "InfoAboutPage.qml"
    }
    */

}