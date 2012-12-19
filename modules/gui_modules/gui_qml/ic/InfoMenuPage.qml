import QtQuick 1.1

// map, ui, POI, navigation, network, debug


IconGridPage {

    InfoPage {
        id : infoPage
    }

    function getPage(menu){
        if (menu == "infoPage") {
            return infoPage
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
            menu : "infoPage"
        }
    }

    Loader {
        id: infoPage1
        source: "InfoPage.qml"
    }

}