import QtQuick 2.0
import UC 1.0
import ".."

BasePage {
    id: layerSelectP
    headerText: qsTr("Select map layer")

    signal layerSelected (string layerId)

    content : ListView {
        id : layerView
        anchors.top : parent.top
        anchors.topMargin : rWin.c.style.main.spacing
        anchors.left : parent.left
        anchors.leftMargin : rWin.c.style.main.spacing/2.0
        anchors.right : parent.right
        anchors.rightMargin : rWin.c.style.main.spacing/2.0
        height : layerSelectP.height - layerSelectP.headerHeight
        clip : true
        currentIndex : -1
        property int itemHeight : rWin.c.style.dialog.item.height
        model : rWin.layerTree
        spacing : rWin.c.style.listView.spacing
        VerticalScrollDecorator {}

        delegate: Component {
            id: listDelegate
            Item {
                id : itemWrapper
                property var dModel : model
                anchors.left : parent.left
                anchors.right : parent.right
                height : groupWrapper.height + layersWrapper.height
                Item {
                    id : groupWrapper
                    anchors.left : parent.left
                    anchors.right : parent.right
                    height : layerView.itemHeight
                    property bool toggled : false
                    property int childrenCount : model.layers.count
                    ThemedBackgroundRectangle {
                        anchors.fill : parent
                        onClicked : {
                            //console.log("group clicked")
                            groupWrapper.toggled = !groupWrapper.toggled
                        }
                    }
                    Label {
                        anchors.verticalCenter : parent.verticalCenter
                        anchors.left : parent.left
                        anchors.leftMargin : rWin.c.style.main.spacingBig * 2
                        text: groupWrapper.toggled ?
                        model.label :
                        model.label + " (" + model.layers.count + ")"
                        font.bold : true
                    }
                }
                Item {
                    id : layersWrapper
                    anchors.left : parent.left
                    anchors.leftMargin : rWin.c.style.main.spacing
                    anchors.right : parent.right
                    anchors.top : groupWrapper.bottom
                    anchors.topMargin : spacing/2.0
                    property real spacing : rWin.c.style.listView.spacing
                    height : groupWrapper.toggled ? layerRepeater.height : 0
                    visible : groupWrapper.toggled
                    Repeater {
                        id : layerRepeater
                        anchors.left : parent.left
                        anchors.right : parent.right
                        model : layersWrapper.visible ? itemWrapper.dModel.layers : 0
                        property int itemHeight : layerView.itemHeight
                        height : groupWrapper.childrenCount * itemHeight
                        Item {
                            id : layerWrapper
                            parent : layerRepeater
                            anchors.left : parent.left
                            anchors.right : parent.right
                            height : layerRepeater.itemHeight
                            y : index * layerRepeater.itemHeight
                            ThemedBackgroundRectangle {
                                anchors.fill : parent
                                anchors.topMargin : layersWrapper.spacing/2.0
                                anchors.bottomMargin : layersWrapper.spacing/2.0
                                onClicked : {
                                    //console.log("layer clicked")
                                    var layerId = model.id
                                    layerSelected(layerId)
                                }
                            }
                            Label {
                                anchors.verticalCenter : parent.verticalCenter
                                anchors.left : parent.left
                                anchors.leftMargin : rWin.c.style.main.spacingBig * 4
                                text: model.label
                                font.bold : true
                            }
                        }
                    }
                }
            }
        }
    }
}