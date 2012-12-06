import QtQuick 1.1
import com.nokia.meego 1.0
import com.nokia.extras 1.0
import Charts 1.0
//import QtMobility.sensors 1.1
//import QtMobility.location 1.1
//import QtMobility.systeminfo 1.1

PageStackWindow {
    // modRana theme
    property string mTheme : options.get("currentTheme", "default")
    id: rWin
    showStatusBar : false
    initialPage : MapPage {
            id: mapPage
        }

    MenuPage {
        id : mainMenu
    }
    OptionsMenuPage {
        id : optionsMenu
    }

    InfoMenuPage {
        id : infoMenu
    }

    MapMenuPage {
        id : mapMenu
    }

    ModeMenuPage {
        id : modeMenu
    }

    /* looks like object ids can't be stored in ListElements,
     so we need this function to return corresponding menu pages
     for names given by a string
    */

    property variant pages : {
        "mainMenu" : mainMenu,
        "optionsMenu" : optionsMenu,
        "infoMenu" : infoMenu,
        "mapMenu" : mapMenu,
        "modeMenu" : modeMenu,
    }

    function getPage(name) {
        return pages[name]
    /* TODO: some pages are not so often visited pages so they could
    be loaded dynamically from their QML files ?
    -> also, a loader pool might be used as a rudimentary page cache,
    but this might not be needed if the speed is found to be adequate */
    }

    property string layer: "mapnik"

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
    }
}
