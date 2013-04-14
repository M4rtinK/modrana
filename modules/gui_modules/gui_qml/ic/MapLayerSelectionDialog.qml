import QtQuick 1.1
//import com.nokia.meego 1.0
import "./qtc"

HeaderDialog {
    id: layerSelectD
    titleText: "Select map layer"

    signal layerSelected (string layerId)
    // close the dialog once a layer is selected
    onLayerSelected : {
        accept()
    }

    //selectedIndex: 1

    content : ListView {
        id : layerView
        model : mapLayersModel
        anchors.fill : parent
        clip : true
        currentIndex : -1
        property int itemHeight : 80
        delegate: Component {
            id: listDelegate
            Item {
                id : itemWrapper
                anchors.left : parent.left
                anchors.right : parent.right
                height : groupWrapper.height + layersWrapper.height
                Item {
                    id : groupWrapper
                    anchors.left : parent.left
                    anchors.right : parent.right
                    height : layerView.itemHeight
                    property bool toggled : false
                    property int childrenCount : model.data.childrenCount
                    Rectangle {
                        anchors.fill : parent
                        color : groupWrapper.toggled ? "darkgray" : "black"
                    }

                    Label {
                        anchors.verticalCenter : parent.verticalCenter
                        anchors.left : parent.left
                        anchors.leftMargin : 32
                        text: groupWrapper.toggled ?
                        model.data.label :
                        model.data.label + " (" + model.data.childrenCount + ")"
                        font.bold : true
                        /*
                        Component.onCompleted : {
                            console.log("CC")
                            console.log(model.data.id)
                            console.log(model.data.label)
                        }*/
                    }
                    MouseArea {
                        id : groupMouseArea
                        anchors.fill : parent
                        onClicked : {
                            //console.log("group clicked")
                            groupWrapper.toggled = !groupWrapper.toggled
                        }
                    }
                }
                Item {
                    id : layersWrapper
                    anchors.left : parent.left
                    anchors.right : parent.right
                    anchors.top : groupWrapper.bottom
                    height : groupWrapper.toggled ? layerRepeater.height : 0
                    visible : groupWrapper.toggled
                    function getLayerLabel(index) {
                        return model.data.getLayerLabel(index)
                    }
                    function getLayerId(index) {
                        return model.data.getLayerId(index)
                    }
                    Repeater {
                        id : layerRepeater
                        anchors.left : parent.left
                        anchors.right : parent.right
                        model : layersWrapper.visible ? groupWrapper.childrenCount : 0
                        property int itemHeight : layerView.itemHeight
                        height : groupWrapper.childrenCount * itemHeight
                        Item {
                            id : layerWrapper
                            parent : layerRepeater
                            anchors.left : parent.left
                            anchors.right : parent.right
                            height : layerRepeater.itemHeight
                            y : index * layerRepeater.itemHeight
                            Rectangle {
                                anchors.fill : parent
                                color : layerMA.pressed ? "darkgray" : "black"
                            }
                            Label {
                                anchors.verticalCenter : parent.verticalCenter
                                anchors.left : parent.left
                                anchors.leftMargin : 64
                                //text: "I'm item " + index
                                text: layersWrapper.getLayerLabel(index)
                                font.bold : true
                            }
                            MouseArea {
                                id : layerMA
                                anchors.fill : parent
                                onClicked : {
                                    //console.log("layer clicked")
                                    var layerId = layersWrapper.getLayerId(index)
                                    layerSelected(layerId)
                                }
                            }

                        }
                    }
                }
            }
        }
    }
}