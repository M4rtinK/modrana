import QtQuick 1.1
//import com.nokia.meego 1.0
import "./qtc"

HeaderDialog {
    id: layerSelectD
    titleText: "Select map layer"


    signal layerSelected (variant selectedLayer)

    //selectedIndex: 1

    content : ListView {
        id : layerView
        model : mapLayersModel
        anchors.left : parent.left
        anchors.right : parent.right
        anchors.top :  parent.top
        //width : layerSelectD.width
        height : layerSelectD.availableHeight
        currentIndex : -1


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
                    height : 50
                    property bool toggled : false
                    property int childrenCount : model.data.childrenCount
                    function getLayer(index) {
                        return model.data.get(index)
                    }

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
                            console.log("group clicked")
                            console.log(groupWrapper.toggled)
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
                    Repeater {
                        id : layerRepeater
                        anchors.left : parent.left
                        anchors.right : parent.right
                        model : groupWrapper.childrenCount
                        property int itemHeight : 50
                        height : groupWrapper.childrenCount * itemHeight
                        Item {
                            id : layerWrapper
                            anchors.left : parent.left
                            anchors.right : parent.right
                            height : layerRepeater.itemHeight
                            y : index * layerRepeater.itemHeight
                            Label {
                                anchors.verticalCenter : parent.verticalCenter
                                anchors.left : parent.left
                                anchors.leftMargin : 64
                                //text: "I'm item " + index
                                text: groupWrapper.getLayer(index).label
                            }
                            MouseArea {
                                anchors.fill : parent
                                onClicked : {
                                    console.log("layer clicked")
                                }
                            }

                        }
                    }
                }
            }
        }
    }


    Component.onCompleted : {
        console.log("Layer selection dialog completed")
        console.log(layerView.height)
        console.log(layerView.width)
        console.log(layerView.count)
        console.log(layerView.currentSection)

    }

    /*
    onSelectedIndexChanged : {
        layerSelected(model.get(selectedIndex))
        accept()
    }*/
}