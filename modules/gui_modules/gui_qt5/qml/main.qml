import QtQuick 2.0
import QtQuick.Window 2.1
import io.thp.pyotherside 1.3
import UC 1.0
import "modrana_components"
import "backend"

ApplicationWindow {
    id : rWin

    title : "modRana"

    property bool startupDone : false
    property bool firstPageLoaded : false
    onFirstPageLoadedChanged : {
        rWin.log.debug(firstPageLoaded)
        if (firstPageLoaded) {
            // hide the startup indicators
            startupLabel.opacity = 0
        }
    }

    // properties
    property alias animate : animateProperty.value
    OptProp {
        id : animateProperty
        value : true
    }

    property alias showBackButton : showBackButtonProperty.value
    OptProp {
        id : showBackButtonProperty
        value : rWin.platform.needsBackButton
    }

    // debugging
    property alias showDebugButton : showDebugButtonProp.value
    OptProp {id: showDebugButtonProp; value : false}
    property alias showUnfinishedPages : showUnfinishedPagesProp.value
    OptProp {id: showUnfinishedPagesProp; value : false}
    property alias tileDebug : tileDebugProperty.value
    OptProp {
        id : tileDebugProperty
        value : false
    }
    property alias locationDebug : locationDebugProp.value
    OptProp {id: locationDebugProp; value : false}

    // logging
    property variant log : PythonLog {}

    property int _landscapeDivider : rWin.platform.needsBackButton ? 5.5 : 8.0
    property int headerHeight : rWin.inPortrait ? height/8.0 : height/_landscapeDivider

    property variant c

    // properties that can be assigned a value
    // by packaging scripts for a given platform
    // -> who would ever want to pass arguments when
    //    running qml file, nonsense! :P
    // tl;dr; If we could easily pass arguments
    // to the QML file with qmlscene or sailfish-qml,
    // hacks like this would not be needed.
    property string _PYTHON_IMPORT_PATH_
    property string _PLATFORM_ID_

    property variant platform : Platform {}

    property alias mapPage : mapPageLoader.item

    Loader {
        id : mapPageLoader
        asynchronous : true
        onLoaded : {
            rWin.log.debug("map page loaded")
            rWin.pushPage(item, null, rWin.animate)
        }
    }

    property variant pages : {
        // pre-load the toplevel pages
        "MapPage" : mapPage
        /*
        "Menu" : loadPage("MenuPage"),
        "OptionsMenu" : loadPage("OptionsMenuPage"),
        "InfoMenu" : loadPage("InfoMenuPage"),
        "MapMenu" : loadPage("MapMenuPage"),
        "ModeMenu" : loadPage("ModeMenuPage"),
        */
    }

    // location
    property variant location : Location {}
    property variant position // full position object
    property variant pos // coordinate only
    // lastGoodPos needs to be always set,
    // by default Brno is used or last known saved position
    // and if available, the last known actual valid position
    property variant lastGoodPos : Coordinate {
        latitude : 49.2
        longitude : 16.616667
        altitude : 237.0
    }
    property real bearing
    // has fix is set to true once fix is acquired
    property bool hasFix : false
    property bool llValid : pos ? pos.isValid : false

    // theme
    property variant theme

    // map layers
    property variant layerTree : ListModel {}
    property variant layerDict

    // actions
    property variant actions : Actions {}

    // are we using qrc ?
    property bool qrc : is_qrc()

    function is_qrc() {
        // Check if modRana is running from qrc by checking the
        // application arguments for the filename of the
        // file that has been started.
        // If it is an so file, it means that we are running from
        // qrc that has been compiled into the so file.
        var full_path = Qt.application.arguments.slice(0,1)[0]
        var filename = full_path.split("/").slice(-1)
        if (filename == "libmodrana-android.so") {
            // As qrc is currently only used on Android,
            // so when when we detect iss used we also setup the Window
            // parameters needed on Android:
            // * window width and height need to be set,
            //   or else only flickering will be seen on
            //   the screen
            // * switch to fullscreen so that the window covers the
            //   whole screen
            // Also when using the sailfish-qml launcher we must *not*
            // set the window size as it wont switch to fullscreen once a size
            // is set.
            rWin.width = 640
            rWin.height = 480
            rWin.setFullscreen(5)  // 5 == fullscreen
            rWin.visible = true
            return true
        } else {
            return false
        }
    }

    // screen
    property var screen: Screen {
        // only prevent screen blanking if modRana is the active application
        keepScreenOn : Qt.application.active && rWin.keepScreenOn
    }

    property alias keepScreenOn : keepScreenOnProp.publicValue
    OptProp {
        // the "internal" modRana value supports multiple
        // modes, so for now we present a bool outside
        // while managing the mode strings in the background
        // and in the future the other modes might also be supported
        // with the Qt 5 GUI
        id: keepScreenOnProp
        value : "always" // we should keep screen on by default
        property bool publicValue : true
        onInitializedChanged : {
            if (keepScreenOnProp.initialized) {
                if (keepScreenOnProp.value == "never") {
                    rWin.log.info("not keeping screen on")
                    keepScreenOnProp.publicValue = false
                } else {
                    rWin.log.info("keeping screen on")
                    keepScreenOnProp.publicValue = true
                }
            }
        }
        // save change to public value to the real value
        onPublicValueChanged : {
            if (keepScreenOnProp.publicValue) {
                keepScreenOnProp.value = "always"
            } else {
                keepScreenOnProp.value = "never"
            }
        }
    }

    // export the Python context so other elements can use
    // it without instantiating it themselves
    property alias python : python

    Component.onCompleted: {
        // start the modRana Python part initialization only once the main Qt 5 GUI
        // element finishes loading so that we can show the "starting up" feedback
        rWin.__import_modRana()
    }

    Component.onDestruction: {
        // for some reason the PyOtherSide atexit handler does not
        // work on Sailfish OS, so we use this
        rWin.log.info("Qt 5 GUI shutdown requested")
        rWin.log.info("notifying Python about shutdown")
        // the Python side shutdown actually runs asynchronously
        // from the QML side shutdown
        rWin.python.call("modrana.gui._shutdown", [])
    }

    Python {
        id : python
        onError: {
            // when an exception is raised, this error handler will be called
            rWin.log.error('python error: ' + traceback);
        }
    }

    Button {
        anchors.top : parent.top
        anchors.right : parent.right
        visible : rWin.showDebugButton
        text : "debug"
        onClicked : {
            rWin.log.info("# starting the Python Debugger (PDB) shell")
            rWin.log.info("# to continue program execution, press c")
            // make sure the pdb module is imported
            python.importModule_sync('pdb')
            // start debugging
            python.call_sync('pdb.set_trace', [])

        }
    }

    Label {
        id : startupLabel
        anchors.horizontalCenter : parent.horizontalCenter
        anchors.verticalCenter : parent.verticalCenter
        font.pixelSize : 32
        text: "<b>starting modRana...</b>"
        horizontalAlignment : Text.AlignHCenter
        verticalAlignment : Text.AlignVCenter
        visible : opacity != 0
        opacity : 0
        Behavior on opacity {
            NumberAnimation { duration: 250*rWin.animate }
        }
        Component.onCompleted : {
                opacity = 1
        }
    }
    ProgressBar {
        anchors.horizontalCenter : parent.horizontalCenter
        anchors.top : startupLabel.bottom
        width : parent.width * 0.8
        indeterminate : true
        opacity : startupLabel.opacity
        visible : startupLabel.visible
    }

    function __import_modRana() {
        // import the modRana module asynchronously and trigger modRana
        // start once the module is loaded

        // import and initialize modRana,
        // taking any import overrides in account
        if (rWin._PYTHON_IMPORT_PATH_) {
            python.addImportPath(rWin._PYTHON_IMPORT_PATH_)
        } else {
            if (rWin.qrc) {
                // we are running on Android and using qrc so
                // add the qrc root to import path
                rWin.log.debug("running on Android")
                rWin.log.debug("adding qrc:/ to Python import path")
                python.addImportPath('qrc:/')
            } else {
                python.addImportPath('.')
            }
        }
        rWin.log.info("importing the modRana Python core")
        python.importModule('modrana', rWin.__start_modRana)
    }

    function __start_modRana() {
        // start modRana asynchronously and trigger Qt 5 GUI initialization
        // once done

        // add Python event handlers
        // - they will be called during modRana startup
        // - like this initial property values will be set
        python.setHandler("themeChanged", function(newTheme){
            rWin.log.info("theme changed to: " + newTheme.name + " (id: " + newTheme.id + ")")
            rWin.theme = newTheme
        })


        // get the argv & remove the qml launcher
        // & qml file name from it (args nr. 0 and 1)
        var argv = Qt.application.arguments.slice(2)

        // add the GUI module id if not in argv
        if (argv.indexOf("-u") == -1) {
            argv = argv.concat(["-u", "qt5"])
        }

        if (rWin._PLATFORM_ID_) {
            if (argv.indexOf("-d") == -1) {
                argv = argv.concat(["-d", rWin._PLATFORM_ID_])
            }
        }
        rWin.log.info('starting the modRana Python core')
        // start modRana
        python.call('modrana.start', [argv], rWin.__init__)
    }

    function __init__() {
        // Do all startup tasks depending on the Python
        // backend being loaded
        rWin.startupDone = true

        // the Python-side logging system should be now up and running
        rWin.log.backendAvailable = true
        rWin.log.info("__init__ running")

        // init miscellaneous other toplevel properties
        animateProperty.key = "QMLAnimate"
        showDebugButtonProp.key = "showQt5GUIDebugButton"
        showUnfinishedPagesProp.key = "showQt5GUIUnfinishedPages"
        tileDebugProperty.key = "showQt5TileDebug"
        locationDebugProp.key = "gpsDebugEnabled"
        keepScreenOnProp.key = "screenBlankingMode"

        // initialize localization
        rWin.location.__init__()

        // load the constants
        // (including the GUI style constants)
        python.call("modrana.gui._getStartupValues", [], rWin.__startup_values_from_modRana)
    }

    function __startup_values_from_modRana(values) {
        // our Python backend returned the values we needed
        rWin.c = values.constants
        rWin.platform.setValuesFromPython(values)
        rWin.log.debug("startup values loaded")

        rWin.log.debug("handling back button display")
        // we need to set showBackButtonProperty here
        // because we need to know if the current platform
        // needs the back button by default or not
        showBackButtonProperty.key = "showQt5BackButton"

        // now check for fullscreen handling
        rWin.log.debug("handling fullscreen state")
        // if on a platform that is not fullscreen-only,
        // set some reasonable default size for the window
        if (!rWin.platform.fullscreenOnly) {
            rWin.width = 640
            rWin.height = 480
        }

        if (!rWin.platform.fullscreenOnly) {
            // no need to trigger fullscreen if the
            // platform is fullscreen only
            if (rWin.platform.shouldStartInFullscreen) {
                rWin.setFullscreen(5) // 5 == fullscreen
            }
        }

        // and now load the map layers
        rWin.log.debug("loading map layers")
        loadMapLayers(values)
        // and initiate asynchronous loading of the map page
        // as it needs to be loaded after
        // location is initialized, so that
        // it picks up the correct position
        // and also once style and other constants
        // such as map layers are also loaded
        rWin.log.debug("loading map page")
        mapPageLoader.source = "MapPage.qml"
    }

    function loadQMLFile(filename, quiet) {
        var component = Qt.createComponent(filename);
        if (component.status == Component.Ready) {
            return component.createObject(rWin);
        } else {
            if (!quiet) {
                rWin.log.error("loading QML file failed: " + filename)
                rWin.log.error("error: " + component.errorString())
            }
            return null
        }
    }

    function loadPage(pageName) {
        rWin.log.info("loading page: " + pageName)
        return loadQMLFile(pageName + ".qml")
    }
    /*
    function loadPage(pageName) {
        rWin.log.info("loading page: " + pageName)
        var component = Qt.createComponent(pageName + ".qml");
        if (component.status == Component.Ready) {
            return component.createObject(rWin);
        } else {
            rWin.log.error("loading page failed: " + pageName + ".qml")
            rWin.log.error("error: " + component.errorString())
            return null
        }
    }
    */

    /* looks like object ids can't be stored in ListElements,
     so we need this function to return corresponding menu pages
     for names given by a string
    */

    function getPage(pageName) {
        rWin.log.debug("GET PAGE")
        rWin.log.debug(pageName)

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
                    rWin.log.debug("page cached: " + pageName)
                } else { // loading failed, go to mapPage
                    newPage = null
                    rWin.log.debug(pageName + " loading failed, using mapPage")
                }
            }
        }
        rWin.log.debug("RETURN PAGE")
        rWin.log.debug(newPage)
        return newPage

    /* TODO: some pages are not so often visited pages so they could
    be loaded dynamically from their QML files ?
    -> also, a loader pool might be used as a rudimentary page cache,
    but this might not be needed if the speed is found to be adequate */
    }

    function push(pageName) {
        // push page by name
        //
        // TODO: instantiate pages that are not in the
        // dictionary
        if (pageName == null) { // null -> back to map
            //TODO: check if the stack can over-fil
            //console.log("BACK TO MAP")
            rWin.pageStack.pop(rWin.mapPage,!animate)
        } else {
            rWin.log.debug("PUSH " + pageName)
            rWin.pushPageInstance(rWin.getPage(pageName))
        }
    }

    function pushPageInstance(pageInstance) {
        // push page instance to page stack
        if (pageInstance) {
            rWin.pushPage(pageInstance, null, rWin.animate)
        } else {
            // page instance not valid, go back to map
            rWin.pageStack.pop(rWin.mapPage, !animate)
        }
    }

    // Working with options
    function get(key, default_value, callback) {
        //rWin.log.debug("get " + callback)
        python.call("modrana.gui.get", [key, default_value], callback)
        return default_value
    }

    function get_auto(key, default_value, target_property) {
        //python.call("modrana.gui.get", [key, default_value], callback)
        console.log("get called")
        console.log(key)
        console.log(default_value)
        console.log(target_property)
        python.call("modrana.gui._get", [key, default_value], function(returned_value) {
            console.log("callback running")
            console.log(target_property)
            console.log(returned_value)
            console.log("done running")
            //target_property=returned_value
            target_property=9001
        })
        return default_value
    }

    function get_sync(key, default_value, callback) {
        return python.call_sync("modrana.gui.get", [key, default_value])
    }

    function set(key, value, callback) {
        python.call("modrana.gui.set", [key, value], function(){
            // there seem to be some issues with proper shutdown
            // so save after set for now
            python.call("modrana.modrana._saveOptions", [])
            if (callback) {
                callback()
            }
        })
    }

    function set_sync(key, value) {
        python.call_sync("modrana.gui.set", [key, value])
        // there seem to be some issues with proper shutdown
        // so save after set for now
        python.call_sync("modrana.modrana.self._saveOptions", [])
    }

    function dcall(functionName, functionArgs, defaultValue, callback) {
        // asynchronous call with immediate default value return
        // * run functionName with functionArgs asynchronously
        // * once the call is dispatched, return default_value
        // * and once the function returns, callback is called
        //
        // The main uses case is to asynchronously initialize properties
        // from Python data once an element is loaded. At first default values are used,
        // that are replaced by the real values once the Python call finishes.
        // Like this, element loading does not have to wait for Python.

        rWin.python.call(functionName, functionArgs, callback)
        return defaultValue
    }

    function loadMapLayers(values) {
        // populate the layer tree
        rWin.layerTree.clear()
        var lTree = values.layerTree
        for (var i=0; i<lTree.length; i++) {
            rWin.layerTree.append(lTree[i])
        }
        rWin.log.info("layer tree loaded")
        // set the layer dict
        rWin.layerDict = values.dictOfLayerDicts
        rWin.log.info("layer dict loaded")
    }

    property variant _lastVisibility

    function toggleFullscreen() {
        // 2 = windowed
        // 3 = minimized
        // 4 = maximized
        // 5 = fullscreen
        // 1 = auto
        // 0 = hidden
        if (rWin.visibility==5) {
            // restore previous state,
            // provided it is not fullscreen
            if(_lastVisibility==5) {
                rWin.visibility = 2
            } else {
                rWin.visibility = rWin._lastVisibility
            }
        } else { // switch to fullscreen
            rWin.visibility = 5
        }
        rWin._lastVisibility = rWin.visibility
    }

    function setFullscreen(value) {
        //TODO: value checking :D
        rWin.visibility = value
        rWin._lastVisibility = rWin.visibility
    }

    function notify(message, timeout) {
        rWin.log.warning("notification skipped (fixme): " + message)
    }
}

