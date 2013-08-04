//OptionsPOIPage.qml

import QtQuick 1.1
import "qtc/PageStatus.js" as PageStatus
import "./qtc"
import com.nokia.meego 1.0

BasePage {
    id: addressSearchPage
    headerText : ""

    headerContent {
        TextField {
            id : searchInput
            anchors.left : parent.left
            anchors.leftMargin : C.style.main.spacing
            anchors.right : parent.right
            anchors.rightMargin : C.style.main.spacingBig
            anchors.top : parent.top
            anchors.topMargin : C.style.main.spacingBig
            anchors.bottom : parent.bottom
            anchors.bottomMargin : C.style.main.spacingBig
            height : parent.height - C.style.main.spacingBig*2
            Component.onCompleted : {
                selectAll()
            }
            Keys.onPressed : {
                if (event.key == Qt.Key_Return || event.key == Qt.Key_Enter){
                    console.log("address search for: " + text)
                    options.set("lastAddressSearchInput", text)
                    search.address(text)
                    console.log(addressSearchModel)
                }
            }
            text : options.get("lastAddressSearchInput", "")
            placeholderText : "address search"
        }
        /*
        Button {
            id : searchButton
            anchors.right : parent.right
            anchors.rightMargin : 8
            anchors.top : parent.top
            anchors.topMargin : 8
            anchors.bottom : parent.bottom
            anchors.bottomMargin : 8
            height : parent.height - 16
            width : 160
            text : "search"
        }*/
    }
    content {
        ListView {
            anchors.top : parent.top
            anchors.topMargin : C.style.listView.spacing
            anchors.left : parent.left
            anchors.right : parent.right
            height : addressSearchPage.availableHeight
            spacing : C.style.listView.spacing
            model : addressSearchModel
            delegate : BackgroundRectangle {
                id : resultDelegate
                anchors.left : parent.left
                anchors.right : parent.right
                height : contentC.height + C.style.listView.itemBorder
                active : resultMA.pressed
                Column {
                    id : contentC
                    anchors.left : parent.left
                    anchors.leftMargin : C.style.main.spacing
                    anchors.verticalCenter : parent.verticalCenter
                    spacing : C.style.main.spacing
                    Label {
                        text : model.data.name
                        font.bold : true
                    }
                    Label {
                        //text : model.data.summary
                        text : model.data.description
                        //elide : Text.ElideRight
                        wrapMode : Text.WordWrap
                        width : resultDelegate.width - C.style.main.spacingBig*2
                    }
                }
                MouseArea {
                    id : resultMA
                    anchors.fill : parent
                    onClicked : {
                        console.log(model.data.name + " clicked")
                        var lat = model.data.lat
                        var lon = model.data.lon
                        rWin.mapPage.showOnMap(lat, lon)
                        rWin.pageStack.pop(null, !rWin.animate)
                    }

                }
            }
        }
        /*
        Label {
            anchors
        }*/

    }
}
