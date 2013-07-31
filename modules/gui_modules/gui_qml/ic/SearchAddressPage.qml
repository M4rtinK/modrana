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
            anchors.leftMargin : 8
            anchors.right : parent.right
            anchors.rightMargin : 8
            anchors.top : parent.top
            anchors.topMargin : 8
            anchors.bottom : parent.bottom
            anchors.bottomMargin : 8
            height : parent.height - 16
            //focus : true
            Keys.onEnterPressed:{
                console.log("address search for: " + text)
                search.address(text)
                console.log("GET")
                console.log(addressSearchModel)
                console.log("GOT?")
            }
            text : ""
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
            anchors.left : parent.left
            anchors.right : parent.right
            height : addressSearchPage.availableHeight
            model : addressSearchModel
            delegate : BackgroundRectangle {
                id : resultDelegate
                anchors.left : parent.left
                anchors.right : parent.right
                height : contentC.height + 20
                active : resultMA.pressed
                Column {
                    id : contentC
                    /*
                    anchors.top : parent.top
                    anchors.topMargin : 10
                    */
                    anchors.left : parent.left
                    anchors.leftMargin : 10
                    anchors.verticalCenter : parent.verticalCenter
                    spacing : 8
                    Label {
                        text : model.data.name
                        font.bold : true
                    }
                    Label {
                        text : model.data.summary
                        elide : Text.ElideRight
                        width : resultDelegate.width - 32
                    }
                }
                MouseArea {
                    id : resultMA
                    anchors.fill : parent
                    onClicked : {
                        console.log(model.data.name + " clicked")
                        var lat = model.data.lat
                        var lon = model.data.lon
                        rWin.mapPage.getMap().setCenterLatLon(lat, lon)
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
