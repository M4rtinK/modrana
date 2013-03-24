import QtQuick 1.1
import "./qtc"
// TODO: add slider to ic/qtc
import com.nokia.meego 1.0


BasePage {
    id: layersPage
    headerText : "Overlays"
    bottomPadding : 32
    isFlickable : false
    property variant model

    //property alias model : layersLW.model

    //property alias model : rWin.mapPage.layers
    content {
        ListView {
            model : rWin.mapPage.layers
            anchors.top : parent.top
            anchors.left : parent.left
            anchors.right : parent.right
            //anchors.bottom : parent.bottom
            //height : 400
            id : layersLW
            height : layersPage.availableHeight

            contentWidth: parent.width
            contentHeight: childrenRect.height

            delegate : Item {
                id : delegateWrapper
                //anchors.fill : parent
                anchors.left : parent.left
                anchors.right : parent.right
                height : lGrid.height + actionGrid.height
                BackgroundRectangle {
                    id : delegateBackground
                    anchors.left : parent.left
                    anchors.right : parent.right
                    // this background only covers the delegates,
                    // the last-item buttons have their own
                    height : lGrid.height
                }


                // is this item the last ?
                property bool isLastItem : index == layersLW.model.count - 1
                Grid {
                    id : lGrid
                    anchors.left : parent.left
                    anchors.right : parent.right
                    anchors.leftMargin : 16
                    anchors.rightMargin : 16
                    columns : parent.inPortrait ? 1 : 2
                    property real cellWidth : width/columns
                    Label {
                        width : lGrid.cellWidth
                        anchors.verticalCenter : parent.verticalCenter
                        property string label : layerId == "" ? "<i>not selected</i>" : "<b>" + layerName + "</b>"
                        text : prefix + label
                        property string prefix : index == 0 ? "map : " : index + " : "
                    }
                    Slider {
                        width : lGrid.cellWidth
                        stepSize : 0.1
                        value : layerOpacity
                        maximumValue : 1.0
                        minimumValue : 0.0
                        valueIndicatorText : (value * 10) + " %"
                        onPressedChanged : {
                            // set the value once users
                            // stops interacting with the slider
                            if (pressed == false) {
                                rWin.mapPage.getMap().setLayerOpacity(index, value)
                            }
                        }
                    }
                }
                Grid {
                    anchors.top : lGrid.bottom
                    anchors.left : parent.left
                    anchors.right : parent.right
                    //height : isLastItem ? lGrid.height : 0
                    id : actionGrid
                    columns : 2
                    property real cellWidth : width/columns
                    visible : isLastItem
                    BackgroundRectangle {
                        width : actionGrid.cellWidth
                        height : isLastItem ? lGrid.height : 0
                        active : addArea.pressed
                        Label {
                            id : addText
                            anchors.verticalCenter : parent.verticalCenter
                            width : parent.width
                            text : "<b>add</b>"
                            horizontalAlignment : Text.AlignHCenter
                        }
                        MouseArea {
                            id : addArea
                            anchors.fill : parent
                            onClicked : {
                                console.log("add layer")
                                console.log(layersLW.height)
                                console.log(layersLW.contentHeight)
                                rWin.mapPage.getMap().appendLayer("openptmap_overlay", "OSM Transit Overlay", 1.0)
                            }
                        }
                    }
                    BackgroundRectangle {
                        width : actionGrid.cellWidth
                        height : isLastItem ? lGrid.height : 0
                        active : removeArea.pressed
                        visible : layersLW.model.count > 1
                        Label {
                            id : removeText
                            anchors.verticalCenter : parent.verticalCenter
                            width : parent.width
                            text : "<b>remove</b>"
                            horizontalAlignment : Text.AlignHCenter
                        }
                        MouseArea {
                            id : removeArea
                            anchors.fill : parent
                            onClicked : {
                                console.log("remove layer")
                                // remove the last layer
                                rWin.mapPage.getMap().removeLayer(layersLW.model.count - 1)
                            }
                        }
                    }
                }
            }
        }
    }
}