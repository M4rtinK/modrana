//OptionsMapPage.qml

import QtQuick 1.1
import "qtc/PageStatus.js" as PageStatus
import "./qtc"
import com.nokia.meego 1.0

BasePage {
    id: compassPage
    headerText : "Map"
    bottomPadding : 0

    content {
        Column {
            anchors.top : parent.top
            anchors.left : parent.left
            anchors.right : parent.right
            anchors.topMargin : C.style.main.spacing
            anchors.leftMargin : C.style.main.spacing
            anchors.rightMargin : C.style.main.spacing
            spacing : C.style.main.spacingBig * 2
            width : parent.width
            Column {
                spacing : C.style.main.spacing
                Label {
                    text : qsTr("Store map tiles in")
                }
                ButtonRow {
                    checkedButton : mapTiles.storageType == "files" ? filesButton : sqliteButton
                    Button {
                        id : filesButton
                        text : "files"
                        onClicked : mapTiles.storageType = "files"

                    }
                    Button {
                        id : sqliteButton
                        text : "Sqlite"
                        onClicked : mapTiles.storageType = "sqlite"
                    }
                }
            }
        }
    }
}
