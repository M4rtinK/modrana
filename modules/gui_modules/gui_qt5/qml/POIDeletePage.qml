//TwoOptionsPage.qml

import QtQuick 2.0
import "modrana_components"

TwoOptionPage {
    id : twoOptionPage
    property var point
    property var pageAbovePOIPage : null
    headerText: twoOptionPage.point.name
    text : qsTr("Delete this POI ?")
    firstButtonText : qsTr("Delete POI")
    firstButtonNormalColor : "red"
    firstButtonHighlightedColor : "orange"
    onFirstButtonClicked : {
        rWin.log.debug("delete POI - confirmed")
        // tell backend to remove the POI from the database
        rWin.python.call("modrana.gui.POI.delete_poi", [twoOptionPage.point.db_id], function(){})
        // remove poi if visible
        rWin.mapPage.removePOIMarkerById(twoOptionPage.point)
        // if we have a reference to the category page, reload its POI listing

        // NOTE: We need to first delete the POI from the database and only then from
        //       the POI marker model. This is because if the user clicked on the
        //       marked and the selected to delete it, the point object would be garbage
        //       collected and would be no longer valid when we try to delete it from
        //       the database. We could likely also void this by caching the db_id value
        //       but this (ordering of actions) works as well. :)

        // go back & out of the POI detail page
        if (pageAbovePOIPage != null) {
            rWin.pop(pageAbovePOIPage)
        } else {
            rWin.pop()
        }
    }
    secondButtonText : qsTr("Cancel")
    onSecondButtonClicked : {
        rWin.log.debug("delete POI - canceled")
        rWin.pop()
    }
}