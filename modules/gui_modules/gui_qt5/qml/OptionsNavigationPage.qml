//OptionsNavigationPage.qml

import QtQuick 2.0
import UC 1.0
import "modrana_components"

BasePage {
    id: optionsNavigationPage
    headerText : "Navigation"

    content : ContentColumn {
        TextSwitch {
            text : qsTr("Enable Routing")
            checked : rWin.mapPage.routingEnabled
            onCheckedChanged : {
                rWin.log.info("changed routing enable: " + checked)
                rWin.mapPage.routingEnabled = checked
            }
        }
    }
}

