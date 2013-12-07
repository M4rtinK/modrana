//OptionsMapPage.qml

import QtQuick 2.0
import UC 1.0

BasePage {
    id: mapOptionsPage
    headerText : "Map"
    bottomPadding : 0

    content {
        Column {
            anchors.top : parent.top
            anchors.left : parent.left
            anchors.right : parent.right
            anchors.topMargin : rWin.c.style.main.spacing
            anchors.leftMargin : rWin.c.style.main.spacing
            anchors.rightMargin : rWin.c.style.main.spacing
            spacing : rWin.c.style.main.spacingBig * 2
            width : parent.width
            Column {
                spacing : rWin.c.style.main.spacing
                Label {
                    text : qsTr("Store map tiles in")
                }
                KeyComboBox {
                    key : "tileStorageType"
                    model : ListModel {
                        ListElement {
                            text : "files"
                            value : "files"

                        }
                        ListElement {
                            text : "Sqlite"
                            value : "sqlite"
                        }
                    }
                }
            }
        }
    }
}
