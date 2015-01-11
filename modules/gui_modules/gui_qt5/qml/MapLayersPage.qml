import QtQuick 2.0
import UC 1.0
import "modrana_components"

BasePage {
    id: layersPage
    headerText : "Overlays"
    bottomPadding : rWin.c.style.main.spacingBig * 2
    isFlickable : false
    property variant model

    content : ListView {
        anchors.top : parent.top
        anchors.topMargin : rWin.c.style.main.spacing
        anchors.left : parent.left
        anchors.right : parent.right
        id : layersLW
        height : layersPage.availableHeight
        spacing : rWin.c.style.listView.spacing

        contentWidth: parent.width
        contentHeight: childrenRect.height

        delegate : Item {
            id : delegateWrapper
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
                anchors.leftMargin : rWin.c.style.main.spacingBig
                anchors.rightMargin : rWin.c.style.main.spacingBig
                columns : rWin.inPortrait ? 1 : 2
                property real cellWidth : width/columns
                Item {
                    id : layerLabelWrapper
                    width : lGrid.cellWidth
                    height : layerLabel.height * 2
                    Label {
                        id : layerLabel
                        width : parent.width
                        elide : Text.ElideRight
                        anchors.verticalCenter : parent.verticalCenter
                        property string label : layerId == "" ? "<i>not selected</i>" : "<b>" + layerName + "</b>"
                        property string prefix : index == 0 ? "map : " : index + " : "
                        text : prefix + label
                    }
                    MouseArea {
                        id : labelMA
                        anchors.fill : parent
                        onClicked : {
                            // open the layer selection dialog
                            // and tell it what is the number of the layer
                            // to be set
                            var layerSelector = Qt.createComponent("MapLayerPage.qml")
                            rWin.pushPage(layerSelector, {layerIndex : index, returnToMap : false}, rWin.animate)
                        }
                    }
                }
                Item {
                    id : sliderWrapper
                    width : lGrid.cellWidth
                    height : opacitySlider.height
                    Slider {
                        id : opacitySlider
                        width : lGrid.cellWidth
                        anchors.verticalCenter : parent.verticalCenter
                        stepSize : 0.1
                        maximumValue : 1.0
                        minimumValue : 0.0
                        value : layerOpacity
                        valueText : ""
                        onPressedChanged : {
                            // set the value once users
                            // stops interacting with the slider
                            if (pressed == false) {
                                rWin.mapPage.getMap().setLayerOpacity(index, value)
                            }
                        }
                    }
                }
            }
            Grid {
                // this grid creates the two bottom
                // add/remove buttons
                id : actionGrid
                anchors.top : lGrid.bottom
                anchors.topMargin : rWin.c.style.listView.spacing
                anchors.left : parent.left
                anchors.right : parent.right
                columns : 2
                spacing : rWin.c.style.listView.spacing
                property real cellWidth : width/columns - spacing/columns
                visible : isLastItem
                Button {
                    width : actionGrid.cellWidth
                    height : isLastItem ? lGrid.height : 0
                    text : "<b>add</b>"
                    onClicked : {
                        console.log("add layer")
                        rWin.mapPage.getMap().appendLayer("openptmap_overlay", "OSM Transit Overlay", 1.0)
                    }
                }
                Button {
                    width : actionGrid.cellWidth
                    height : isLastItem ? lGrid.height : 0
                    visible : layersLW.model.count > 1
                    text : "<b>remove</b>"
                    onClicked : {
                        console.log("remove layer")
                        // remove the last layer
                        rWin.mapPage.getMap().removeLayer(layersLW.model.count - 1)
                    }
                }
            }
        }
        // for some reason the Silica Slider won't set the highlight position
        // properly if the model is set as the same time as the list view
        // is instantiated - race condition ?
        Component.onCompleted : {
            model = rWin.mapPage.layers
        }
    }
}