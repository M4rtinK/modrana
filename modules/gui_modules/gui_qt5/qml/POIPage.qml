//PointPage.qml

import QtQuick 2.0
import UC 1.0
import "modrana_components"
import "functions.js" as F

BasePage {
    id: poiPage
    headerText : point.name
    property var point
    property real distanceToPoint : F.p2pDistance(poiPage.point, rWin.lastGoodPos)
    headerMenu : TopMenu {
        MenuItem {
            text : qsTr("Show on map")
            onClicked : {
                rWin.log.info("Show POI on map: " + point.name)
                var poiModel = rWin.mapPage.getMap().poiMarkerModel
                // first check if we already have the POI in the model
                var alreadyAdded = false
                for (var i=0; i<poiModel.count; i++) {
                    if (poiModel.get(i).db_id == point.db_id) {
                        alreadyAdded = true
                        break
                    }
                }
                if (!alreadyAdded) {
                    rWin.log.debug("adding POI to map list model: " + point.name)
                    // We need to create a new point instance like this,
                    // or else the original point instance might get garbage collected,
                    // causing issues later.
                    poiModel.append({
                        "name" : point.name,
                        "description" : point.description,
                        "latitude" : point.latitude,
                        "longitude" : point.longitude,
                        "elevation" : point.elevation,
                        "highlight" : false,
                        "mDistance" : 0,
                        "db_id" : point.db_id,
                        "category_id" : point.category_id
                    })
                }
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
    }
}
