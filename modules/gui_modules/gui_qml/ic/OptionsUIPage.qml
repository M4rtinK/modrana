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
            anchors.top : parent.top
            anchors.topMargin : 8
            spacing : 30
            width : parent.width
            Column {
                spacing : 10
                Label {
                    text : qsTr("Theme")
                }
                // once more themes are available,
                // use a picker button ?
                ButtonRow {
                    checkedButton : modrana.theme_id == "default" ? defaultButton : nightButton
                    Button {
                        id : defaultButton
                        text : "default"
                        onClicked : modrana.theme_id = "default"

                    }
                    Button {
                        id : nightButton
                        text : "night"
                        onClicked : modrana.theme_id = "night"
                    }
                }
            }
        }
    }
}
