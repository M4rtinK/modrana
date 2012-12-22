import QtQuick 1.1

// map, ui, POI, navigation, network, debug


IconGridPage {

    InfoAboutPage {
        id : aboutPage
    }
    InfoSpeedPage {
        id : speedPage
    }

    function getPage(menu){
        if (menu == "aboutPage") {
            return aboutPage
        } else if (menu = "speedPage") {
            return speedPage
        }
    }

    isMockup: false
    model : ListModel {
        id : testModel
        /*
        ListElement {
            caption : "Compass"
            icon : "windrose-simple.svg"
            menu : ""
        }
        */
        ListElement {
            caption : "Speed"
            icon : "info.png"
            menu : "speedPage"
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