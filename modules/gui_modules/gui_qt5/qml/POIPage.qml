//PointPage.qml

import QtQuick 2.0
import UC 1.0
import "modrana_components"

BasePage {
    id: poiPage
    headerText : point.name
    property var point


    headerMenu : TopMenu {
        MenuItem {
            text : "Show on map"
            onClicked : {
                rWin.log.info("Show POI on map: " + point.name)
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
                text : "<b>latitude:</b> " + point.latitude
            }
            Label {
                text : "<b>longitude:</b> " + point.longitude
            }
        }
   }
}
