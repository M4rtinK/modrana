import QtQuick 2.0
import "modrana_components"

Markers {
    id : markers
    delegate: Component {
        Item {
            Bubble {
                anchors.horizontalCenter : pointMarker.horizontalCenter
                anchors.bottom : pointMarker.top
                anchors.bottomMargin : 8
                z: 2000
                bubbleWidth : childrenRect.width + rWin.c.style.map.button.margin*2
                bubbleHeight : childrenRect.height + rWin.c.style.map.button.margin*2

                MapButton {
                    id: routeHere
                    z: 2000
                    text: qsTr("<b>route here</b>")
                    x : rWin.c.style.map.button.margin
                    y : rWin.c.style.map.button.margin
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
            Marker {
                id : pointMarker
                point: model
                targetPoint: markers.mapInstance.getScreenpointFromCoord(model.latitude, model.longitude)
                //verticalSpacing: model.numSimilar
                z: 2000
                //TODO: use a constant/make this configurable ?
                simple : markers.mapInstance.zoomLevel < 13
            }
        }
    }
}
