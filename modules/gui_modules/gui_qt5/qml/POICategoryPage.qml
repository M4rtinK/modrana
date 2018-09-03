//POICategoryPage.qml

import QtQuick 2.0
import UC 1.0
import "modrana_components"
import "functions.js" as F

BasePage {
    id: pcPage
    property string categoryName
    property int categoryId

    headerText : qsTr(categoryName)

    // make sure the category listing is reloaded
    // when the POI database changes
    Connections {
        target : rWin
        onPoiDatabaseChanged : {
            reloadCategory()
        }
    }

    content : ContentColumn {
        ListView {
            id : itemsLW
            anchors.left : parent.left
            anchors.right : parent.right
            height : pcPage.maxContentHeight
            spacing : rWin.c.style.listView.spacing
            model : ListModel {
               id : resultsModel
            }
            clip : true
            VerticalScrollDecorator {}
            delegate : ThemedBackgroundRectangle {
                id : resultDelegate
                width : itemsLW.width
                height : contentC.height + rWin.c.style.listView.itemBorder
                property string distanceString : F.formatDistance(F.p2pDistance(model, rWin.lastGoodPos), 1)
                onClicked : {
                    rWin.log.info("POI category list: " + model.name + " clicked")

                    // switch to page listing tracklogs for the given category
                    var poiPage = rWin.loadPage("POIPage", {"point" : model,
                                                            "previousPage" : pcPage})
                    rWin.pushPageInstance(poiPage)
                }
                Column {
                    id : contentC
                    anchors.left : parent.left
                    anchors.leftMargin : rWin.c.style.main.spacing
                    anchors.verticalCenter : parent.verticalCenter
                    spacing : rWin.c.style.main.spacing
                    Label {
                        text : "<b>" + model.name + "</b> (" + resultDelegate.distanceString + ")"
                    }
                    Label {
                        text : model.latitude + ", " + model.latitude
                    }
                }
            }
        }
    }

    function reloadCategory() {
        rWin.log.debug("reloading category " + pcPage.categoryId)
        rWin.python.call("modrana.gui.POI.get_all_poi_from_category", [pcPage.categoryId], function(poiList){
            itemsLW.model.clear()
            for (var i=0; i<poiList.length; i++) {
                itemsLW.model.append(poiList[i]);
            }
        })
    }

    // TODO: move somewhere else & execute earlier
    onCategoryIdChanged : {
        reloadCategory()
    }
}