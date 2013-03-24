import QtQuick 1.1

// map, ui, POI, navigation, network, debug


IconGridPage {

    isMockup : false

    function getPage(menu){
        modrana.mode = menu
        rWin.push(null)
    }


    //TODO: get mode list from modRana core
    model : ListModel {
        id : testModel
        ListElement {
            caption : "Foot"
            icon : "walk.png"
            menu : "walk"
        }
        ListElement {
            caption : "Car"
            icon : "car.png"
            menu : "car"
        }
        ListElement {
            caption : "Cycle"
            icon : "cycle.png"
            menu : "cycle"
        }
        ListElement {
            caption : "Bus"
            icon : "bus.png"
            menu : "bus"
        }
        ListElement {
            caption : "Train"
            icon : "train.png"
            menu : "train"
        }
    }
}