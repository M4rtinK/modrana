import QtQuick 2.0

Item {
    property bool valid : false
    property string modRanaVersion : "unknown"
    property bool show_quit_button : true
    property bool fullscreen_only : false
    property bool should_start_in_fullscreen : false
    property bool needs_back_button : true
    property bool needs_page_background : false
    // location specific
    property var lastKnownPos : null
    property bool gpsEnabled : true
    property var posFromFile : null
    property var nmeaFilePath : null
    property string themesFolderPath : "unknown_path"
    property bool sailfish : false

    function setValuesFromPython(values) {
        modRanaVersion = values.modRanaVersion
        show_quit_button = values.show_quit_button
        fullscreen_only = values.fullscreen_only
        should_start_in_fullscreen = values.should_start_in_fullscreen
        needs_back_button = values.needs_back_button
        needs_page_background = values.needs_page_background
        lastKnownPos = values.lastKnownPos
        gpsEnabled = values.gpsEnabled
        posFromFile = values.posFromFile
        nmeaFilePath = values.nmeaFilePath
        themesFolderPath = values.themesFolderPath
        sailfish = values.sailfish
        // done, we now have the values from Python we needed
        valid = true
    }
}
