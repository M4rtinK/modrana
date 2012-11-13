import QtQuick 1.1
//import com.nokia.meego 1.0
import "./qtc"

// map, ui, POI, navigation, network, debug


IconGridPage {

    isMockup : false

    function getPage(menu){
        options.set('mode', menu)
        return null
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