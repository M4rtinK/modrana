import QtQuick 1.1

// map, ui, POI, navigation, network, debug


IconGridPage {

    InfoAboutPage {
        id : aboutPage
    }

    function getPage(menu){
        if (menu == "aboutPage") {
            return aboutPage
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