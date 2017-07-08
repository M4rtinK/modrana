//PointPage.qml

import QtQuick 2.0
import UC 1.0
import "modrana_components"

BasePage {
    id: savePointPage
    headerText : qsTr("Save POI")
    property var point
    property int categoryId : 11

    headerMenu : TopMenu {
        MenuItem {
            text : qsTr("Confirm and save")
            onClicked : {
                rWin.log.debug("saving point: " + point.name)
                var pointDict = {
                    "name" : point.name,
                    "description" : point.description,
                    "lat" : point.latitude,
                    "lon" : point.longitude,
                    "category_id" : savePointPage.categoryId
                }
                python.call("modrana.gui.POI.store_poi", [pointDict], function(success) {
                    rWin.pop()
                    if (success) {
                        rWin.notify(qsTr("POI saved"), 3000)
                    } else {
                        rWin.notify(qsTr("POI could not be saved"), 3000)
                    }

                })
            }
        }
    }
    content : ContentColumn {
        Label {
            text : qsTr("Name")
            width : parent.width
            wrapMode : Text.WordWrap
        }
        TextInput {
            text : point.name
            width : parent.width
            wrapMode : TextInput.WordWrap
        }
        Label {
            text : qsTr("Description")
            width : parent.width
            wrapMode : Text.WordWrap
        }
        TextInput {
            text : point.description
            width : parent.width
            wrapMode : TextInput.WordWrap
        }
        Label {
            text : qsTr("Category")
            width : parent.width
            wrapMode : Text.WordWrap
        }
        ComboBox {
            id : catCombo
            width : parent.width
            currentIndex: 10
            model: ListModel {
                id: cbItems // TODO: load categories dynamically
                    ListElement { text: qsTr("Service station"); category_id: 1 }
                    ListElement { text: qsTr("Residence"); category_id: 2 }
                    ListElement { text: qsTr("Restaurant"); category_id: 3 }
                    ListElement { text: qsTr("Shopping/Services"); category_id: 4 }
                    ListElement { text: qsTr("Recreation"); category_id: 5 }
                    ListElement { text: qsTr("Transportation"); category_id: 6 }
                    ListElement { text: qsTr("Lodging"); category_id: 7 }
                    ListElement { text: qsTr("School"); category_id: 8 }
                    ListElement { text: qsTr("Business"); category_id: 9 }
                    ListElement { text: qsTr("Landmark"); category_id: 10 }
                    ListElement { text: qsTr("Other"); category_id: 11 }
            }
            onCurrentIndexChanged: {
                rWin.log.debug(cbItems.get(currentIndex).text + ", " + cbItems.get(currentIndex).category_id)
                savePointPage.categoryId = cbItems.get(currentIndex).category_id
            }
        }
    }
}
