import QtQuick 1.1
import com.nokia.meego 1.0


// map, ui, POI, navigation, network, debug



IconGridPage {
    function getPage(menu){
        if (menu == "mapDialog") {
            layerSelectD.open()
        }
    }

    model : ListModel {
        id : testModel
        ListElement {
            caption : "Layer"
            icon : "map_layers.png"
            menu : "mapDialog"
        }
        ListElement {
            caption : "Download"
            icon : "download.png"
            menu : ""
        }
    }


    SelectionDialog {
        id: layerSelectD
        titleText: "Select map layer"
        //selectedIndex: 1

        /*delegate: Rectangle {
            //width: parent.width
            height: 80
            color: index%2?"#eee":"#ddd"
            Label {
                id: title
                elide: Text.ElideRight
                //text: model.get(index).caption
                text: "TEST"
                color: "white"
                font.bold: true
                anchors.leftMargin: 10
                anchors.fill: parent
                verticalAlignment: Text.AlignVCenter
            }
            MouseArea {
                anchors.fill: parent
                onClicked: {
                    //rWin.setLayer(model.get(index).name)
                    rWin.setLayer(model.get(selectedIndex).name)
                    rWin.pageStack.pop(null)
                    accept()
                }
            }

        }*/

        onSelectedIndexChanged : {
            rWin.setLayer(model.get(selectedIndex).layerID)
            //rWin.pageStack.pop()
            rWin.pageStack.pop(null)
            accept()
            }

        model: ListModel {
            ListElement { name: "OSM Mapnik"; layerID: "mapnik" }
            ListElement { name: "OSM Cycle map"; layerID: "cycle" }
            ListElement { name: "Google map"; layerID: "gmap" }
            ListElement { name: "Google satellite"; layerID: "gsat" }
            ListElement { name: "Google overlay"; layerID: "gover" }
            ListElement { name: "Google 8-bit"; layerID: "g8bit" }
            ListElement { name: "Virtual Earth map"; layerID: "vmap" }
            ListElement { name: "Virtual Earth satellite"; layerID: "vsat" }
            ListElement { name: "Yahoo map"; layerID: "ymap" }
            ListElement { name: "Yahoo satellite"; layerID: "ysat" }
            ListElement { name: "Yahoo overlay"; layerID: "yover" }
            ListElement { name: "Czech mountain-bike map"; layerID: "cz_mtb" }
        }
    }
}