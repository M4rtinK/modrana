import QtQuick 2.0

// on map marker display support - "abstract class" part

Item {
    id: markerContainer
    property var mapInstance

    property variant model : ListModel {}

    property var delegate

    Repeater {
        id : markerR
        model : markerContainer.model
        delegate : markerContainer.delegate
    }

    function clear() {
        // clear all markers
        markerContainer.model.clear()
    }

    function appendMarker(lat, lon, name, highlight) {
        if (!highlight) {
            highlight = false
        }
        if (!name) {
            name = ""
        }
        markerContainer.model.append({"latitude": lat, "longitude" : lon, "name":name, "highlight" : highlight})
    }

    function appendMarkers(markerList) {
        // append the given marker list to our model
        for (var i=0; i<markerList.count; i++) {
            var item = markerList.get(i)
            markerContainer.model.appendMarker(item.latitude, item.longitude, item.highlight)
        }

    }

    function removeMarker(markerIndex) {
        markerContainer.model.remove(markerIndex)
    }

    function setMarker(markerIndex, markerDict) {
        markerContainer.model.set(markerIndex, markerDict)
    }

    function setMarkers(markersModel) {
        // set the marker list model to markersModel
        markerContainer.model = markersModel
    }

    function setMarkerHighlight(markerIndex, value) {
        // set the value of the highlight property for the marker on the given index
        markerContainer.model.setProperty(markerIndex, "highlight", value)
    }

    function clearAllHighlights() {
        // unhighlight all markers
        for (var i=0; i<markerContainer.model.count; i++) {
            setMarkerHighlight(i, false)
        }
    }
}