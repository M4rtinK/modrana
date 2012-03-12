import QtQuick 1.1
import com.nokia.meego 1.0
import com.nokia.extras 1.0

PageStackWindow {
    property string theme : options.get("currentTheme", "default")
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

    /* looks like object ids can't be stored in ListElements,
     so we need this function to return corresponding menu pages
     for names given by a string
    */

    property variant pages : {
        "mainMenu" : mainMenu,
        "optionsMenu" : optionsMenu,
        "infoMenu" : infoMenu
    }

    function getPage(name) {
        return pages[name]
    /* TODO: some pages are not so often visited pages so they could
    be loaded dynamically from their QML files ?
    -> also, a loader pool might be used as a rudimentary page cache,
    but this might not be needed if the speed is found to be adequate */
    }

    /** global notification handling **/
    InfoBanner {
        id: notification
        timerShowTime : 5000
        height : rWin.height/5.0
        // prevent overlapping with status bar
        y : rWin.showStatusBar ? rWin.statusBarHeight + 8 : 8

    }
}
