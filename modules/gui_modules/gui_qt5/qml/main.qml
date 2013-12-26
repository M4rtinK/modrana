import QtQuick 2.0
import QtQuick.Window 2.1
import io.thp.pyotherside 1.0
import UC 1.0

ApplicationWindow {
    id : rWin
    width : 640
    height : 480

    title : "modRana"

    // properties
    property string guiID : "unknown"

    property bool animate : true

    property bool showDebugButton : false

    property variant c

    Loader {
        id : platformLoader
    }
    //property variant platform : platformLoader.item
    property variant platform

    property variant mapPage

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
    // by defaultBrno is used or last known saved position
    // and if available, the last known actual valid position
    property variant lastGoodPos : Coordinate {
        latitude : 49.2
        longitude : 16.616667
        altitude : 237.0
    }
    property real bearing
    property bool llValid : pos.isValid

    // theme
    property variant theme

    // export the Python context so other elements can use
    // it without instantiating it themselves
    property alias python : python
    Python {
        id : python
        Component.onCompleted: {
            // add Python event handlers
            // - they will be called during
            //   modRana startup
            // - like this initial values will be set
            python.setHandler("themeChanged", function(newTheme){
                console.log("THEME CHANGED !!!!")
                rWin.theme = newTheme
            })
            // import and initialize modRana
            addImportPath('.');
            //importModule('pdb', function() {})
            importModule_sync('sys')
            importModule_sync('pdb')
            importModule_sync('modrana')
            // fake the argv
            //call_sync('setattr','sys' , 'argv' ,'["modrana.py", "-u", "qt5", "-d", "pc"]')
            evaluate('setattr(sys, "argv" ,["modrana.py", "-u", "qt5", "-d", "pc"])')
            console.log('sys.argv faked')
            call_sync('modrana.start')
            //guiID = evaluate("modrana.gui.getIDString()")
            call("modrana.gui.getIDString", [], function(result){
                guiID = result
            })

        }

        onError: {
            // when an exception is raised, this error handler will be called
            console.log('python error: ' + traceback);
        }
    }

    Button {
        anchors.bottom : parent.bottom
        anchors.right : parent.right
        visible : rWin.showDebugButton
        text : "debug"
        onClicked : {
            //console.log(rWin.set("speedTest", 1337))
            //console.log(rWin.get_sync("speedTest", 1234))
            //console.log(rWin.get("speed", 120, function(value){speedMS = value}))
            //console.log(speedMS)
            console.log(rWin.get_sync("speedTest", 1234))
            //console.log(python.evaluate('modrana.gui.get("speedTest")'))
            console.log(python.evaluate('pdb.set_trace()'))

        }
    }

    // everything should be initialized by now,
    // including the Python backend
    Component.onCompleted: {
        rWin.__init__()
    }

    function __init__() {
        // Do all startup tasks depending on the Python
        // backend being loaded
        console.log("__init__ running")

        // load the constants
        // (including the GUI style constants)
        rWin.c = python.call_sync("modrana.gui.getConstants", [])

        // init miscellaneous other toplevel properties
        rWin.animate = rWin.get_sync("QMLAnimate", true)
        rWin.showDebugButton = rWin.get_sync("showQt5GUIDebugButton", false)

        // the various property encapsulation items need the
        // Python backend to be initialized, so we can load them now
        //platformLoader.source = "Platform.qml"
        rWin.platform = loadQMLFile("Platform.qml")
        _init_location()

        // the map page needs to be loaded after
        // location is initialized, so that
        // it picks up the correct position
        rWin.mapPage = loadPage("MapPage")
        rWin.initialPage = rWin.mapPage
    }

    function _init_location() {
        // initialize the location module,
        // this also start localisation,
        // if enabled
        rWin.location.__init__()
    }

    //property variant mapPage : loadPage("MapPage")

    function loadQMLFile(filename, quiet) {
        var component = Qt.createComponent(filename);
        if (component.status == Component.Ready) {
            return component.createObject(rWin);
        } else {
            if (!quiet) {
                console.log("loading QML file failed: " + filename)
                console.log("error: " + component.errorString())
            }
            return null
        }
    }

    function loadPage(pageName) {
        console.log("loading page: " + pageName)
        return loadQMLFile(pageName + ".qml")
    }
    /*
    function loadPage(pageName) {
        console.log("loading page: " + pageName)
        var component = Qt.createComponent(pageName + ".qml");
        if (component.status == Component.Ready) {
            return component.createObject(rWin);
        } else {
            console.log("loading page failed: " + pageName + ".qml")
            console.log("error: " + component.errorString())
            return null
        }
    }
    */

    /* looks like object ids can't be stored in ListElements,
     so we need this function to return corresponding menu pages
     for names given by a string
    */

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
            rWin.pageStack.pop(null,!animate)
        } else {
            console.log("PUSH " + pageName)
            rWin.pageStack.push(getPage(pageName),null,!rWin.animate)
        }
    }

    // Working with options
    function get(key, default_value, callback) {
        //console.log("running " + callback)
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

    function set(key, value) {
        python.call("modrana.gui.set", [key, value])
    }

    function set_sync(key, value) {
        python.call_sync("modrana.gui.set", [key, value])
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
}

