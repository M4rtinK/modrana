//PointPage.qml

import QtQuick 2.0
import UC 1.0
import "modrana_components"

BasePage {
    id: pointPage
    headerText : point.name
    property var point

    headerMenu : TopMenu {
        MenuItem {
            text : qsTr("Local search")
            onClicked : {
                rWin.log.info("Local search: " + point.latitude + "," + point.longitude)
                var searchPage = rWin.loadPage("SearchLocalPage", {"searchPoint" : point})
                rWin.pushPageInstance(searchPage)
            }
        }
        MenuItem {
            text : qsTr("Save")
            onClicked : {
                rWin.log.info("Save POI: " + point.name)
                var pointPage = rWin.loadPage("SavePointPage", {"point" : point})
                rWin.pushPageInstance(pointPage)
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
