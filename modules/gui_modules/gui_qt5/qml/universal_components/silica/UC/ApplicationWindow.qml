import QtQuick 2.0
import Sailfish.Silica 1.0
ApplicationWindow{
    property bool inPortrait : deviceOrientation == Orientation.Portrait ||
                               deviceOrientation == Orientation.PortraitInverted
    property bool inverted : deviceOrientation == Orientation.PortraitInverted ||
                             deviceOrientation == Orientation.LandscapeInverted

    // The whole Silica ApplicationWindow does not rotate on orientation change.
    // This is a difference from for example the Qt Quick Controls ApplicationWindow,
    // where the whole Window rotates.
    property bool rotatesOnOrientationChange : false

    cover : null

    function orientationToString(o) {
        switch (o) {
        case Orientation.Portrait:
            return "portrait"
        case Orientation.Landscape:
            return "landscape"
        case Orientation.PortraitInverted:
            return "inverted portrait"
        case Orientation.LandscapeInverted:
            return "inverted landscape"
        }
        return "unknown"
    }

    onDeviceOrientationChanged : {
        var orientationName = orientationToString(deviceOrientation)
        console.log("device orientation changed to: " + orientationName + " (" + deviceOrientation + ")")
    }

    // this property is provided for API compatibility
    // as the Silica UC backend uses the Silica built-in
    // element sizing
    property int hiDPI : 0

    // the Silica ApplicationWindow
    // does not inherit the Window element,
    // so we need to add some properties
    // for a common API with Controls
    property string title
    property var visibility : 5

    function pushPage(pageInstance, pageProperties, animate) {
        var animateFlag
        if (animate) {
            animateFlag = PageStackAction.Animated
        } else {
            animateFlag = PageStackAction.Immediate
        }
        pageStack.push(pageInstance, pageProperties, animateFlag)
        return pageInstance
    }
}
