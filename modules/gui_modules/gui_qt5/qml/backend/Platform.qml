import QtQuick 2.0

Item {
    property bool valid : false
    property string modRanaVersion : "unknown"
    property bool showQuitButton : true
    property bool fullscreenOnly : false
    property bool shouldStartInFullscreen : false
    property bool needsBackButton : true
    property bool needsPageBackground : false
    // location specific
    property var lastKnownPos : null
    property bool gpsEnabled : true
    property var posFromFile : null
    property var nmeaFilePath : null
    property string themesFolderPath : "unknown_path"
    property bool sailfish : false

    function setValuesFromPython(values) {
        modRanaVersion = values.modRanaVersion
        showQuitButton = values.showQuitButton
        fullscreenOnly = values.fullscreenOnly
        shouldStartInFullscreen = values.shouldStartInFullscreen
        needsBackButton = values.needsBackButton
        needsPageBackground = values.needsPageBackground
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