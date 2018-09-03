//PointPage.qml

import QtQuick 2.0
import UC 1.0
import "modrana_components"
import "functions.js" as F

BasePage {
    id: poiPage
    headerText : point.name
    property var point
    property var previousPage : null
    property real distanceToPoint : F.p2pDistance(poiPage.point, rWin.lastGoodPos)
    headerMenu : TopMenu {
        MenuItem {
            text : qsTr("Show on map")
            onClicked : {
                rWin.log.info("Show POI on map: " + point.name)
                rWin.mapPage.addPOIMarker(point)
                rWin.mapPage.showOnMap(point.latitude, point.longitude)
                rWin.push(null, !rWin.animate)
            }
        }
        MenuItem {
            text : qsTr("Local search")
            onClicked : {
                rWin.log.info("Local search: " + point.latitude + "," + point.longitude)
                var searchPage = rWin.loadPage("SearchLocalPage", {"searchPoint" : point})
                rWin.pushPageInstance(searchPage)
            }
        }
        MenuItem {
            text : qsTr("Route here")
            onClicked : {
                rWin.log.info("Route to POI: " + point.name + " " + point.latitude + "," + point.longitude)
                rWin.mapPage.routeToPoint(point)
                rWin.push(null, !rWin.animate)
            }
        }
    }
    content : ContentColumn {
        Label {
            text : point.description
            width : parent.width
            wrapMode : Text.WordWrap
        }
        SmartGrid {
            Label {
                text : qsTr("<b>latitude:</b>") + " " + point.latitude
            }
            Label {
                text : qsTr("<b>longitude:</b>") + " " + point.longitude
            }
        }
        Label {
            text : "<b>" + qsTr("distance") + ":</b>" + " " + F.formatDistance(poiPage.distanceToPoint, 1)
        }
        Button {
            text : qsTr("Delete POI from database")
            anchors.horizontalCenter : parent.horizontalCenter
            onClicked : {
                var deletePOIPage = rWin.loadPage("POIDeletePage", {"point" : point,
                                                                    "pageAbovePOIPage" : previousPage})
                rWin.pushPageInstance(deletePOIPage)
            }
        }
    }
}
