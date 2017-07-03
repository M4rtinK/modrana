import QtQuick 2.0

POIMarkers {
    onPoiClicked : {
        rWin.log.info("POI clicked: " + point.name)
        var pointPage = rWin.loadPage("PointPage", {"point" : point})
        rWin.pushPageInstance(pointPage)
    }
}
