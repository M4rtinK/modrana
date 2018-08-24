//SearchPage.qml

import QtQuick 2.0
import UC 1.0
import ".."
import "../modrana_components"
import "../functions.js" as F

HeaderPage {
    id: searchPage
    // search type id
    property string searchId : ""
    property string pageHeader : ""
    property string _searchResultId : "search:result:"  + searchId
    property string _searchStatusId : "search:status:" + searchId
    property var searchPoint: null
    // persistent dict key that should be used to store and retrieve
    // last used search query
    height : rWin.c.style.button.generic.height
    property string lastSearchKey : ""
    property bool _searchInProgress : false
    property string _searchStatus : ""
    property string _searchThreadId : ""
    property bool showNavigationIndicator : false

    function search (query) {
        rWin.python.call("modrana.gui.search.search", [searchPage.searchId, query, searchPoint], function(threadId) {
            rWin.log.info("searching for: " + query + " using " + searchPage.searchId)
            searchPage._searchThreadId = threadId
            searchPage._searchInProgress = true
        })
    }

    Component.onCompleted : {
        // connect to the status & result callbacks
        rWin.python.setHandler(searchPage._searchStatusId, function(v){
            rWin.log.info("search status: " + v)
            searchPage._searchStatus = v
        })
        rWin.python.setHandler(searchPage._searchResultId, function(results){
            rWin.log.info("search result: " + results)
            // load the results into a list model
            // (for some reason just assigning it does not work)
            pointLW.model.clear()
            for (var i=0; i<results.length; i++) {
                pointLW.model.append(results[i]);
            }
            // first set distance for all results
            pointLW.setDistance()
            // then sort them by the distance
            pointLW.model.sort()
            // TODO: we might want to re-do the sort
            //       when position changes or when the
            //       results screen is re-visited
            searchPage._searchInProgress = false
        })
    }

    Item {
        id : progressInfo
        anchors.left : parent.left
        anchors.leftMargin : rWin.c.style.main.spacing/2.0
        anchors.right : parent.right
        anchors.rightMargin : rWin.c.style.main.spacing/2.0
        opacity : 0.0
        state : searchPage._searchInProgress ? "ON" : "OFF"
        y : rWin.headerHeight + rWin.c.style.listView.spacing / 2.0

        ThemedBackgroundRectangle {
            anchors.left : parent.left
            anchors.right : cancelButton.left
            anchors.rightMargin : rWin.c.style.main.spacing
            width : progressInfo.width - cancelButton.width - spacing * 2
            height : progressInfo.height
            Label {
                text : searchPage._searchStatus
                elide : Text.ElideRight
                fontSizeMode: Text.HorizontalFit
                horizontalAlignment : Text.AlignHCenter
                anchors.verticalCenter : parent.verticalCenter
                anchors.left : parent.left
                anchors.leftMargin : rWin.c.style.main.spacing
                anchors.right : parent.right
                anchors.rightMargin : rWin.c.style.main.spacing
            }
        }
        Button {
            id : cancelButton
            anchors.right : parent.right
            text : qsTr("Cancel")
            height : progressInfo.height
            onClicked : {
                rWin.log.info("search: cancel pressed")
                rWin.python.call("modrana.gui.search.cancelSearch",
                                 [searchPage._searchThreadId],
                                 function(){
                                    searchPage._searchInProgress = false
                                 })
            }
        }

        onStateChanged : {
            rWin.log.info("search: progress state changed: " + state)
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
                     NumberAnimation { target: progressInfo; property: "height"; to: rWin.headerHeight ; duration: 200*rWin.animate}
                     NumberAnimation { target: progressInfo; property: "opacity"; to: 1.0; duration: 200*rWin.animate}
                 },
                 Transition {
                     from: "ON"
                     to: "OFF"
                     NumberAnimation { target: progressInfo; property: "height"; to: 0; duration: 200*rWin.animate}
                     NumberAnimation { target: progressInfo; property: "opacity"; to: 0.0; duration: 200*rWin.animate}
                 }
             ]


    }
    SearchField {
        id : searchInput
        anchors.left : parent.left
        anchors.leftMargin : rWin.showBackButton ? backButtonWidth + 24 * rWin.c.style.m : rWin.c.style.main.spacingBig
        anchors.right : parent.right
        anchors.rightMargin : rWin.c.style.main.spacingBig
        anchors.top : parent.top
        anchors.topMargin : rWin.c.style.main.spacing
        height : rWin.headerHeight - rWin.c.style.main.spacing*2
        placeholderText: qsTr("enter your search query")
        Component.onCompleted : {
            selectAll()
        }
        Keys.onPressed : {
            if (event.key == Qt.Key_Return || event.key == Qt.Key_Enter){
                // turn off the virtual keyboard (if any) if there is some text in the search field
                if (text !== "") {
                    focus = false
                }

                rWin.log.info("address search for: " + text)
                if (searchPage.lastSearchKey != "") {
                    rWin.log.info("search: saving " + text)
                    rWin.set(searchPage.lastSearchKey, text)
                }
                searchPage.search(text)
            }
        }
        text : rWin.get(searchPage.lastSearchKey, "", function(v){searchInput.text=v})
    }

    ListView {
        id : pointLW
        anchors.top : progressInfo.bottom
        anchors.topMargin : rWin.c.style.listView.spacing / 2.0
        anchors.left : parent.left
        anchors.leftMargin : rWin.c.style.main.spacing/2.0
        anchors.right : parent.right
        anchors.rightMargin : rWin.c.style.main.spacing/2.0
        height : searchPage.maxContentHeight
        spacing : rWin.c.style.listView.spacing
        model : SortableListModel {
           id : resultsModel
           // we want to sort the search results by distance
           // TODO: maybe an option to turn this OFF and use the
           //       ordering from the search provider ?
           //       In some cases that could be the preferred option.
           //       Or maybe a UI option in on the page to switch
           //       how the results are sorted.
           sortKeyName : "mDistance"
        }
        clip : true
        VerticalScrollDecorator {}

        function setDistance(result) {
            // set distance from current position for all results in the list
            for (var i=0; i<model.count; i++) {
                model.setProperty(i, "mDistance", F.p2pDistance(model.get(i),
                                                  rWin.lastGoodPos))
            }
        }

        delegate : ThemedBackgroundRectangle {
            id : resultDelegate
            width : pointLW.width
            height : contentC.height + rWin.c.style.listView.itemBorder
            // a string describing distance from current position to the result
            property string distanceString : F.formatDistance(model.mDistance, 1)

            onClicked : {
                rWin.log.info("search:" + model.name + " clicked")
                // mark the current point as highlighted so that it
                // is highlighted once it id displayed on the map
                pointLW.model.setProperty(index, "highlight", true)

                // set the current search result model content
                // for display on the map
                rWin.mapPage.clearSearchMarkers()
                for (var i=0; i<pointLW.model.count; i++) {
                    rWin.mapPage.addSearchMarker(pointLW.model.get(i))
                }

                var lat = model.latitude
                var lon = model.longitude
                rWin.mapPage.showOnMap(lat, lon)
                rWin.push(null)
            }
            Column {
                id : contentC
                anchors.left : parent.left
                anchors.leftMargin : rWin.c.style.main.spacing
                anchors.verticalCenter : parent.verticalCenter
                spacing : rWin.c.style.main.spacing
                Label {
                    text : "<b>" + model.name + "</b> (" + resultDelegate.distanceString + ")"
                }
                Label {
                    text : model.description
                    wrapMode : Text.WordWrap
                    width : resultDelegate.width - rWin.c.style.main.spacingBig*2
                }
            }
        }
    }
}
