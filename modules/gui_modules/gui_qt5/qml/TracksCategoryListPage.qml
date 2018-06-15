//TracksRecordPage.qml

import QtQuick 2.0
import UC 1.0
import "modrana_components"

BasePage {
    id: tclPage

    headerText : qsTr("Categories")

    content : ContentColumn {
        ListView {
            id : itemsLW
            anchors.left : parent.left
            anchors.right : parent.right
            height : tclPage.maxContentHeight
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
                    rWin.log.info("tracklog category list: " + model.name + " clicked")

                    // switch to page listing tracklogs for the given category
                    var categoryPage = rWin.getPage("TracksCategory")
                    categoryPage.categoryName = model.name
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
                        function getTracklogString(tracklogCount) {
                            if (tracklogCount <= 0) {
                                return qsTr("no tracklogs")
                            } else if (tracklogCount == 1) {
                                return 1 + " " + qsTr("tracklog")
                            } else {
                                return tracklogCount + " " + qsTr("tracklogs")
                            }
                        }
                        text : getTracklogString(model.tracklog_count)
                        wrapMode : Text.WordWrap
                        width : resultDelegate.width - rWin.c.style.main.spacingBig*2
                    }
                }
            }
        }
    }


    // TODO: move somewhere else & execute earlier
    Component.onCompleted : {
        rWin.python.call("modrana.gui.modules.loadTracklogs.get_category_dict_list", [], function(categories){
            itemsLW.model.clear()
            for (var i=0; i<categories.length; i++) {
                itemsLW.model.append(categories[i]);
            }
        })
    }
}
