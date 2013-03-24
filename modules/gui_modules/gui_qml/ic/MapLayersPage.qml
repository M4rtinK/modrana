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
            anchors.bottom : parent.bottom
            id : layersLW
            height : parent.availableHeight
            delegate : BackgroundRectangle {
                id : delegateWrapper
                //anchors.fill : parent
                anchors.left : parent.left
                anchors.right : parent.right
                height : isLastItem ? lGrid.height + actionGrid.height : lGrid.height
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
                        property string label : layerId == "" ? "<i>not selected</i>" : layerId
                        text : prefix + label
                        property string prefix : index == 0 ? "<b>main map</b> " : "<b>overlay " + index + "</b> "
                    }
                    Slider {
                        width : lGrid.cellWidth
                        stepSize : 0.1
                        value : layerOpacity
                        maximumValue : 1.0
                        minimumValue : 0.0
                        valueIndicatorText : (value * 10) + " %"
                    }
                }
                Grid {
                    anchors.top : lGrid.bottom
                    anchors.left : parent.left
                    anchors.right : parent.right
                    id : actionGrid
                    columns : 2
                    property real cellWidth : width/columns
                    visible : isLastItem
                    BackgroundRectangle {
                        width : actionGrid.cellWidth
                        height : lGrid.height
                        active : addArea.pressed
                        Label {
                            id : addText
                            anchors.verticalCenter : parent.verticalCenter
                            width : parent.width
                            text : "<b>add</b>"
                            horizontalAlignment : Text.AlignHCenter
                            MouseArea {
                                id : addArea
                                anchors.fill : parent
                                onClicked : {
                                    console.log("add layer")
                                }
                            }
                        }
                    }
                    BackgroundRectangle {
                        width : actionGrid.cellWidth
                        height : lGrid.height
                        active : removeArea.pressed
                        Label {
                            id : removeText
                            anchors.verticalCenter : parent.verticalCenter
                            width : parent.width
                            text : "<b>remove</b>"
                            horizontalAlignment : Text.AlignHCenter
                            MouseArea {
                                id : removeArea
                                anchors.fill : parent
                                onClicked : {
                                    console.log("remove layer")
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}