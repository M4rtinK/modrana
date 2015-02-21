import QtQuick 2.0

// on map marker display support

Item {
    id: markerContainer
    property var mapInstance
    Repeater {
        id : markersR
        delegate: Marker {
            point: model
            targetPoint: mapInstance.getMappointFromCoord(model.latitude, model.longitude)
            //verticalSpacing: model.numSimilar
            z: 2000
            //TODO: use a constant/make this configurable ?
            simple : mapInstance.zoomLevel < 13
        }
    }

    function clear() {
        // clear all markers
        markersR.model.clear()
    }

    function addMarker(lat, lon) {
        //TODO: implement this

    }

    function removeMarker(markerIndex) {
        //TODO: implement this

    }

    function setMarkers(markersModel) {
        // set the marker list model to markersModel

        markersR.model = markersModel
    }

    function appendMarkers(markers) {
        //TODO: implement this

    }

    function setMarkerHighlight(markerIndex) {
        //TODO: implement this

    }

    function clearAllHighlights() {
        //TODO: implement this

    }

}