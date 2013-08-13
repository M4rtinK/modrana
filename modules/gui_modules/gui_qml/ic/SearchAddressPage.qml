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
        Item {
            id : progressInfo
            //anchors.top : parent.top
            //anchors.topMargin : C.style.main.spacing
            anchors.left : parent.left
            anchors.right : parent.right
            property real progressH : C.style.button.generic.height
            //height : search.addressInProgress ? progressH : 0
            //visible : search.addressInProgress
            state : "OFF"
            height : progressH
            y : -progressH
            Row {
                spacing : C.style.main.spacing
                TextButton {
                    text : search.addressStatus
                    height : progressInfo.height
                    width : progressInfo.width * 3/4
                }
                TextButton {
                    text : "Cancel"
                    height : progressInfo.height
                    width : progressInfo.width * 1/4 - C.style.main.spacing
                    onClicked : {
                        console.log("Cancel pressed")
                        search.addressCancel()
                    }
                }
            }

             Connections {
                 target: search
                 onAddressInProgressChanged: {
                    progressInfo.state = search.addressInProgress ? "ON" : "OFF"
                 }
             }


            onStateChanged : {
                console.log("STATE CHANGED: " + state)
            }

            states: [
                     State {
                         name: "ON"
                     },
                     State {
                         name: "OFF"
                     }
                 ]

                 transitions: [
                     Transition {
                         from: "OFF"
                         to: "ON"
                         NumberAnimation { target: progressInfo; property: "y"; to: C.style.main.spacing; duration: 200*rWin.animate}
                     },
                     Transition {
                         from: "ON"
                         to: "OFF"
                         NumberAnimation { target: progressInfo; property: "y"; to: -progressInfo.progressH; duration: 200*rWin.animate}
                     }
                 ]


        }
        ListView {
            id : pointLW
            anchors.top : progressInfo.bottom
            anchors.topMargin : C.style.listView.spacing
            anchors.left : parent.left
            anchors.right : parent.right
            height : addressSearchPage.availableHeight
            spacing : C.style.listView.spacing
            model : addressSearchModel
            clip : true
            delegate : BackgroundRectangle {
                id : resultDelegate
                width : pointLW.width
                //anchors.left : pointLW.left
                //anchors.right : pointLW.right
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
