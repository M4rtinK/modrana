import QtQuick 2.0

Markers {
    id : markers
    delegate: Component {
        Marker {
            point: model
            targetPoint: markers.mapInstance.getScreenpointFromCoord(model.latitude, model.longitude)
            //verticalSpacing: model.numSimilar
            z: 2000
            //TODO: use a constant/make this configurable ?
            simple : markers.mapInstance.zoomLevel < 13
        }
    }
}
