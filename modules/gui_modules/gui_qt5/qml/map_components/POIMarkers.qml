import QtQuick 2.0
import UC 1.0
import "../modrana_components"

Markers {
    id : markers
    signal poiClicked(var point)
    delegate: Component {
        Marker {
            id : poiMarker
            point: model
            targetPoint: markers.mapInstance.getScreenpointFromCoord(model.latitude, model.longitude)
            z: 2000
            Bubble {
                id : poiBubble
                visible: markers.mapInstance.zoomLevel > 13
                anchors.verticalCenter : parent.verticalCenter
                anchors.left : parent.right
                property int bubbleMargin : 8 * rWin.c.style.m
                anchors.leftMargin : rWin.c.style.map.button.margin / 4.0
                bubbleType : poiBubble.rightBubble
                z: 2000
                bubbleWidth : poiButton.width + rWin.c.style.map.button.margin
                bubbleHeight : poiButton.height + rWin.c.style.map.button.margin

                MapTextButton {
                    id: poiButton
                    z: 2000
                    text: "<b>" + model.name + "</b>"
                    anchors.right : parent.right
                    anchors.rightMargin : rWin.c.style.map.button.margin / 2.0
                    anchors.top : parent.top
                    anchors.topMargin : rWin.c.style.map.button.margin / 2.0
                    onClicked: {
                        markers.poiClicked(model)
                    }
                }
            }
        }
    }
}
