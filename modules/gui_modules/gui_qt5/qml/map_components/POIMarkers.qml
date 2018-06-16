import QtQuick 2.0
import UC 1.0
import "../modrana_components"

Markers {
    id : markers
    property real mapButtonSize : 80
    property real mapButtonSpacing : 10
    signal poiClicked(var point)
    delegate: Component {
        Item {
            Marker {
                id : poiMarker
                point: model
                targetPoint: markers.mapInstance.getScreenpointFromCoord(model.latitude, model.longitude)
                z: 2000
            }
            Bubble {
                id : poiBubble
                visible: markers.mapInstance.zoomLevel > 13
                anchors.verticalCenter : poiMarker.verticalCenter
                anchors.left : poiMarker.right
                anchors.leftMargin : rWin.c.style.map.button.margin / 4.0
                bubbleType : poiBubble.rightBubble
                z: 2000
                bubbleWidth : childrenRect.width + mapButtonSpacing * 2
                bubbleHeight : childrenRect.height + mapButtonSpacing * 2

                MapTextButton {
                    id: poiButton
                    z: 2000
                    anchors.right : parent.right
                    anchors.rightMargin : mapButtonSpacing
                    anchors.top : parent.top
                    anchors.topMargin : mapButtonSpacing
                    text: "<b>" + model.name + "</b>"
                    height: mapButtonSize
                    margin: mapButtonSize * 0.2
                    onClicked: {
                        markers.poiClicked(model)
                    }
                }
            }
        }
    }
}
