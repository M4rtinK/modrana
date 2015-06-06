import QtQuick 2.0

Markers {
    id : markers
    Repeater {
        id : markersR
        model : markers.model
        delegate: Marker {
            point: model
            Component.onCompleted : {
                console.log("test")
            }
            //targetPoint: markers.mapInstance.getMappointFromCoord(modelData.latitude, modelData.longitude)
            //verticalSpacing: model.numSimilar
            z: 2000
            //TODO: use a constant/make this configurable ?
            simple : markers.mapInstance.zoomLevel < 13
        }
    }
}
