import QtQuick 1.1
import com.nokia.meego 1.0

// map, ui, POI, navigation, network, debug



IconGridPage {
    function getPage(menu){
        if (menu = "mapDialog") {
            singleSelectionDialog.open()
        }
    }

    model : ListModel {
        id : testModel
        ListElement {
            caption : "Layer"
            icon : "map.png"
            menu : "mapDialog"
        }
        ListElement {
            caption : "Download"
            icon : "download.png"
            menu : ""
        }
    }


    SelectionDialog {
       id: singleSelectionDialog
       titleText: "Dialog Header #1"
       //selectedIndex: 1

       onSelectedIndexChanged : {
           rWin.setLayer(model.get(selectedIndex).name)
           //rWin.pageStack.pop()
           rWin.pageStack.pop()
           accept()
           }

       model: ListModel {
           ListElement { name: "mapnik" }
           ListElement { name: "gmap" }
           ListElement { name: "gsat" }
           ListElement { name: "gover" }
           ListElement { name: "vmap" }
           ListElement { name: "vsat" }
           ListElement { name: "yover" }
           ListElement { name: "cycle" }
           ListElement { name: "cz_mtb" }
           }
    }
}