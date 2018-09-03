import QtQuick 2.0
import "../modrana_components"

Markers {
    id : markers
    property real mapButtonSize : 80
    property real mapButtonSpacing : 10
    delegate: Component {
        Item {
            Bubble {
                anchors.horizontalCenter : pointMarker.horizontalCenter
                anchors.bottom : pointMarker.top
                anchors.bottomMargin : mapButtonSpacing * 0.75
                z: 2000
                bubbleWidth : childrenRect.width + mapButtonSpacing * 2
                bubbleHeight : childrenRect.height + mapButtonSpacing * 2

                Column {
                    spacing : mapButtonSpacing * 0.75
                    x : rWin.c.style.map.button.margin
                    y : rWin.c.style.map.button.margin
                    MapTextButton {
                        id: pintInfo
                        z: 2000
                        anchors.horizontalCenter : parent.horizontalCenter
                        text: qsTr("<b>Point info</b>")
                        height: mapButtonSize
                        margin: mapButtonSize * 0.2
                        onClicked: {
                            rWin.log.info("showing info for on-map point")
                            var pointPage = rWin.loadPage("PointPage", {"point" : model,
                                                                        "namePlaceholder" : qsTr("A point on the map"),
                                                                        "descriptionPlaceholder" : qsTr("An arbitrary point on the map."),
                                                                        "returnToMapOnSave" : true})
                            rWin.pushPageInstance(pointPage)
                        }
                    }
                    MapTextButton {
                        id: routeHere
                        z: 2000
                        anchors.horizontalCenter : parent.horizontalCenter
                        text: qsTr("<b>Route here</b>")
                        height: mapButtonSize
                        margin: mapButtonSize * 0.2
                        onClicked: {
                            rWin.log.info("routing to a point on the map")
                            rWin.mapPage.routeToPoint(model)
                            rWin.mapPage.clearPointMenus()
                        }
                    }
                }
            }
            Marker {
                id : pointMarker
                point: model
                targetPoint: markers.mapInstance.getScreenpointFromCoord(model.latitude, model.longitude)
                //verticalSpacing: model.numSimilar
                z: 2000
            }
        }
    }
}
