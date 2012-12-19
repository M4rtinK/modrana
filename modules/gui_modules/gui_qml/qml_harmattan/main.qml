import QtQuick 1.1
import "../ic" 1.0
import com.nokia.meego 1.0
import com.nokia.extras 1.0
import Charts 1.0
import "../ic/Pager.js" as Pager
//import QtMobility.sensors 1.1
//import QtMobility.location 1.1
//import QtMobility.systeminfo 1.1

PageStackWindow {
    // modRana theme
    property string mTheme : options.get("currentTheme", "default")
    id: rWin
    showStatusBar : false


    initialPage : mapPage
    //property variant mapPage : Pager.loadPage("MapPage", rWin)
    property variant mapPage : loadPage("MapPage")

    function loadPage(pageName) {
        return Pager.loadPage(pageName, rWin)
    }

    /* looks like object ids can't be stored in ListElements,
     so we need this function to return corresponding menu pages
     for names given by a string
    */

    property variant pages : {
        // pre-load the toplevel pages
        "MapPage" : mapPage,
        "Menu" : loadPage("MenuPage"),
        "OptionsMenu" : loadPage("OptionsMenuPage"),
        "InfoMenu" : loadPage("InfoMenuPage"),
        "MapMenu" : loadPage("MapMenuPage"),
        "ModeMenu" : loadPage("ModeMenuPage"),
    }

    function getPage(pageName) {
        console.log("GET PAGE")
        console.log(pageName)

        var newPage
        if (pageName == null) { //signal that we should return to the map page
            newPage = mapPage
        } else { // load a page
            var fullPageName = pageName + "Page"
            newPage = pages[pageName]
            if (!newPage) { // is the page cached ?
                // load the page and cache it
                newPage = loadPage(fullPageName)
                if (newPage) { // loading successful
                    pages[pageName] = newPage // cache the page
                } else { // loading failed, go to mapPage
                    newPage = mapPage
                }
            }
        }
        return newPage

    /* TODO: some pages are not so often visited pages so they could
    be loaded dynamically from their QML files ?
    -> also, a loader pool might be used as a rudimentary page cache,
    but this might not be needed if the speed is found to be adequate */
    }

    function push(pageName) {
        // TODO: instantiate pages that are not in the
        // dictionary
        if (pageName == null) { // null -> back to map
            //TODO: check if the stack can over-fil
            //console.log("BACK TO MAP")
            rWin.pageStack.push(mapPage)
        } else {
            console.log("PUSH " + pageName)
            rWin.pageStack.push(getPage(pageName))
        }
    }

    property string layer: "mapnik"

    property string foo : "bar"

    function setLayer(name) {
        layer = name
    }

    /** global notification handling **/
    function notify(text, msTimeout) {
        notification.text = text
        notification.timerShowTime = msTimeout
        notification.show()
    }


    /*
    PieChart {
        id: chart
        anchors.centerIn: parent
        width: 100; height: 100
        pieSlice: PieSlice {
            anchors.fill: parent
            color: "red"
        }
    }
    */

    InfoBanner {
        id: notification
        timerShowTime : 5000
        height : rWin.height/5.0
        // prevent overlapping with status bar
        y : rWin.showStatusBar ? rWin.statusBarHeight + 8 : 8

    }

    /*
    // compass
    Compass {
        id: compass
        onReadingChanged: {azimuth = compass.reading.azimuth; calibration = compass.reading.calibrationLevel; }
        property real azimuth: 0
        property real calibration: 0
        active: true
        dataRate: 10
    }


    // temporary position source
    PositionSource {
        id: gpsSource
        active: true
        updateInterval: 1000
        onPositionChanged: {
            console.log("lat: " + position.coordinate.latitude + "lon: " + position.coordinate.longitude )
            controller.positionChanged(position.latitudeValid, position.coordinate.latitude, position.coordinate.longitude, position.altitudeValid, position.coordinate.altitude, position.speedValid, position.speed, position.horizontalAccuracy, position.timestamp);
        }
    }
    */


    Component.onCompleted : {

        //pageStack.push(mPage)
    }


}
