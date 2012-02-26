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

    /** global notification handling **/
    InfoBanner {
        id: notification
        timerShowTime : 5000
        height : rWin.height/5.0
        // prevent overlapping with status bar
        y : rWin.showStatusBar ? rWin.statusBarHeight + 8 : 8

    }
}
