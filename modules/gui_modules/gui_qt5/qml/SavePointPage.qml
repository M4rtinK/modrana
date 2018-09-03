//PointPage.qml

import QtQuick 2.0
import UC 1.0
import "modrana_components"

BasePage {
    id: savePointPage
    headerText : qsTr("Save POI")
    property var point
    property bool returnToMap : false
    property int categoryId : 11

    headerMenu : TopMenu {
        MenuItem {
            text : qsTr("Confirm and save")
            onClicked : {
                if (!point.name) {
                    rWin.notify(qsTr("POI name not set"), 3000)
                    return
                }
                rWin.log.debug("saving point: " + point.name)
                var pointDict = {
                    "name" : point.name,
                    "description" : point.description,
                    "lat" : point.latitude,
                    "lon" : point.longitude,
                    "category_id" : savePointPage.categoryId
                }
                python.call("modrana.gui.POI.store_poi", [pointDict], function(success) {
                    if (returnToMap) {
                        rWin.push(null)
                    } else {
                        rWin.pop()
                    }
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
        TextField {
            text : point.name
            onTextChanged : {
                point.name = text
            }
            width : parent.width
        }
        Label {
            text : qsTr("Description")
            width : parent.width
            wrapMode : Text.WordWrap
        }
        TextArea {
            text : point.description
            onTextChanged : {
                point.description = text
            }
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
            translationContext : "POICategoryName"
            width : parent.width
            currentIndex: 10
            model: ListModel {
                id: cbItems // TODO: load categories dynamically
                    ListElement { text: QT_TRANSLATE_NOOP("POICategoryName", "Service station"); category_id: 1 }
                    ListElement { text: QT_TRANSLATE_NOOP("POICategoryName", "Residence"); category_id: 2 }
                    ListElement { text: QT_TRANSLATE_NOOP("POICategoryName", "Restaurant"); category_id: 3 }
                    ListElement { text: QT_TRANSLATE_NOOP("POICategoryName", "Shopping/Services"); category_id: 4 }
                    ListElement { text: QT_TRANSLATE_NOOP("POICategoryName", "Recreation"); category_id: 5 }
                    ListElement { text: QT_TRANSLATE_NOOP("POICategoryName", "Transportation"); category_id: 6 }
                    ListElement { text: QT_TRANSLATE_NOOP("POICategoryName", "Lodging"); category_id: 7 }
                    ListElement { text: QT_TRANSLATE_NOOP("POICategoryName", "School"); category_id: 8 }
                    ListElement { text: QT_TRANSLATE_NOOP("POICategoryName", "Business"); category_id: 9 }
                    ListElement { text: QT_TRANSLATE_NOOP("POICategoryName", "Landmark"); category_id: 10 }
                    ListElement { text: QT_TRANSLATE_NOOP("POICategoryName", "Other"); category_id: 11 }
            }
            onCurrentIndexChanged: {
                rWin.log.debug(cbItems.get(currentIndex).text + ", " + cbItems.get(currentIndex).category_id)
                savePointPage.categoryId = cbItems.get(currentIndex).category_id
            }
        }
    }
}
