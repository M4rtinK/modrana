import QtQuick 1.1
//import com.nokia.meego 1.0
import "./qtc"

SelectionDialog {
    id: layerSelectD
    titleText: "Select map layer"

    signal layerSelected (variant selectedLayer)

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
                rWin.push(null)
                accept()
            }
        }

    }*/

    onSelectedIndexChanged : {
        layerSelected(model.get(selectedIndex))
        accept()
    }

    model: ListModel {
        ListElement { name: "OSM Mapnik"; layerId: "mapnik" }
        ListElement { name: "OSM Cycle map"; layerId: "cycle" }
        ListElement { name: "OSM Transit overlay"; layerId: "openptmap_overlay" }
        ListElement { name: "Google map"; layerId: "gmap" }
        ListElement { name: "Google satellite"; layerId: "gsat" }
        ListElement { name: "Google overlay"; layerId: "gover" }
        ListElement { name: "Google 8-bit"; layerId: "g8bit" }
        ListElement { name: "Google Traffic"; layerId: "gtraffic_overlay" }
        ListElement { name: "Google Weather °C"; layerId: "gweather_overlay_celsius" }
        ListElement { name: "Virtual Earth map"; layerId: "vmap" }
        ListElement { name: "Virtual Earth hybrid"; layerId: "vsat" }
        ListElement { name: "Virtual Earth satellite"; layerId: "vaer" }
        ListElement { name: "Yahoo map"; layerId: "ymap" }
        ListElement { name: "Yahoo satellite"; layerId: "ysat" }
        ListElement { name: "Yahoo overlay"; layerId: "yover" }
        ListElement { name: "Czech mountain-bike map"; layerId: "cz_mtb" }
        ListElement { name: "map1.eu"; layerId: "map1_eu" }
        ListElement { name: "Watercolor"; layerId: "stamen_watercolor" }
    }
}