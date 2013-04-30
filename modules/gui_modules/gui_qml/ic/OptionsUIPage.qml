//OptionsUIPage.qml

import QtQuick 1.1
import "qtc/PageStatus.js" as PageStatus
import "./qtc"
import com.nokia.meego 1.0

BasePage {
    id: optionsUIPage
    headerText : "UI"

    content {
        Column {
            spacing : 30
            width : parent.width
            LineText {
                width : parent.width
                text : qsTr("Theme")
            }
            // once more themes are available,
            // use a picker button ?
            ButtonRow {
                Button {
                    text : "default"
                    onClicked : modrana.theme_id = "default"

                }
                Button {
                    text : "night"
                    onClicked : modrana.theme_id = "night"
                }
            }

        }
    }
}
