//TracksRecordPage.qml

import QtQuick 2.0
import UC 1.0
import "modrana_components"

BasePage {
    id: tcPage

    property string categoryName : qsTr("unknown")

    headerText : categoryName

    content : ContentColumn {
        ListView {
            id : itemsLW
            anchors.left : parent.left
            anchors.right : parent.right
            height : tcPage.maxContentHeight
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
                    rWin.log.info("tracklog category page: " + model.name + " clicked")
                    rWin.python.call("modrana.gui.modules.loadTracklogs.get_tracklog_points_for_path", [model.path], function(tracklog){
                        // show the tracklog on the map
                        rWin.mapPage.showTracklog(tracklog)
                    })
                    rWin.push(null)
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
                    // TODO: add tracklog details
                    Label {
                        text : model.size + " " + qsTr("kB")
                        wrapMode : Text.WordWrap
                        width : resultDelegate.width - rWin.c.style.main.spacingBig*2
                    }
                }
            }
        }
    }

    // TODO: move somewhere else & execute earlier
    onCategoryNameChanged : {
        rWin.python.call("modrana.gui.modules.loadTracklogs.get_tracklogs_list_for_category", [categoryName], function(categories){
            itemsLW.model.clear()
            for (var i=0; i<categories.length; i++) {
                itemsLW.model.append(categories[i]);
            }
        })
    }
}
