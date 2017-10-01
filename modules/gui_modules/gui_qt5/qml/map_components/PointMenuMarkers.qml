import QtQuick 2.0
import "../modrana_components"

Markers {
    id : markers
    delegate: Component {
        Item {
            Bubble {
                anchors.horizontalCenter : pointMarker.horizontalCenter
                anchors.bottom : pointMarker.top
                anchors.bottomMargin : 8 * rWin.c.style.m
                z: 2000
                bubbleWidth : childrenRect.width + rWin.c.style.map.button.margin*2
                bubbleHeight : childrenRect.height + rWin.c.style.map.button.margin*2

                Column {
                    spacing : 8 * rWin.c.style.m
                    x : rWin.c.style.map.button.margin
                    y : rWin.c.style.map.button.margin
                    MapButton {
                        id: pintInfo
                        z: 2000
                        text: qsTr("<b>Point info</b>")
                        width: rWin.c.style.map.button.size * 2.5
                        height: rWin.c.style.map.button.size
                        onClicked: {
                            rWin.log.info("showing info for on-map point")
                            model.name = "A point on the map"
                            model.description = "An arbitrary point on the map."
                            var pointPage = rWin.loadPage("PointPage", {"point" : model})
                            rWin.pushPageInstance(pointPage)
                        }
                    }
                    MapButton {
                        id: routeHere
                        z: 2000
                        text: qsTr("<b>Route here</b>")
                        width: rWin.c.style.map.button.size * 2.5
                        height: rWin.c.style.map.button.size
                        onClicked: {
                            rWin.log.info("routing from last good position to a point on the map")
                            rWin.mapPage.setRoutingStart(rWin.lastGoodPos.latitude, rWin.lastGoodPos.longitude)
                            rWin.mapPage.setRoutingDestination(model.latitude, model.longitude)
                            rWin.mapPage.routing.requestRoute()
                            rWin.mapPage.enableRoutingUI(false)
                            rWin.mapPage.getMap().clearPointMenus()
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
