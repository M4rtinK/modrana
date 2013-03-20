import QtQuick 1.1
//import com.nokia.meego 1.0
import "./qtc"

SelectionDialog {
    id: layerSelectD
    titleText: "Select map layer"

    signal layerSelected (string selectedLayer)

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
        layerSelected(model.get(selectedIndex).layerID)
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
        ListElement { name: "Virtual Earth hybrid"; layerID: "vsat" }
        ListElement { name: "Virtual Earth satellite"; layerID: "vear" }
        ListElement { name: "Yahoo map"; layerID: "ymap" }
        ListElement { name: "Yahoo satellite"; layerID: "ysat" }
        ListElement { name: "Yahoo overlay"; layerID: "yover" }
        ListElement { name: "Czech mountain-bike map"; layerID: "cz_mtb" }
    }
}