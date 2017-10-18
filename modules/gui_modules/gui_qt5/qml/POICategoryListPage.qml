//TracksRecordPage.qml

import QtQuick 2.0
import UC 1.0
import "modrana_components"

BasePage {
    id: pclPage

    headerText : qsTr("POI Categories")

    content : ContentColumn {
        ListView {
            id : itemsLW
            anchors.left : parent.left
            anchors.right : parent.right
            height : pclPage.maxContentHeight
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

                onClicked : {
                    rWin.log.info("POI category list: " + model.name + " clicked")

                    // switch to page listing tracklogs for the given category
                    var categoryPage = rWin.getPage("POICategory")
                    categoryPage.categoryId = model.category_id
                    rWin.pushPageInstance(categoryPage)
                }
                Column {
                    id : contentC
                    anchors.left : parent.left
                    anchors.leftMargin : rWin.c.style.main.spacing
                    anchors.verticalCenter : parent.verticalCenter
                    spacing : rWin.c.style.main.spacing
                    Label {
                        text : "<b>" + model.name + "</b>"
                    }
                    Label {
                        text : model.poi_count + " " + qsTr("POIs")
                        wrapMode : Text.WordWrap
                        width : resultDelegate.width - rWin.c.style.main.spacingBig*2
                    }
                }
            }
        }
    }

    // TODO: move somewhere else & execute earlier
    Component.onCompleted : {
        rWin.python.call("modrana.gui.POI.list_used_categories", [], function(categories){
            itemsLW.model.clear()
            for (var i=0; i<categories.length; i++) {
                itemsLW.model.append(categories[i]);
            }
        })
    }
}
