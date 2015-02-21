import QtQuick 2.0
import Sailfish.Silica 1.0
ApplicationWindow{
    property bool inPortrait : _setOrientation(deviceOrientation)

    onDeviceOrientationChanged : {
        _setOrientation(deviceOrientation)
    }

    cover : null

    /*
    cover: CoverBackground {
        CoverPlaceholder {
            text: "modRana"
        }
    }*/

    // this property is provided for API compatibility
    // as the Silica UC backend uses the Silica built-in
    // element sizing
    property int hiDPI : 0

    function _setOrientation(dOrient) {
        if (dOrient == Orientation.Portrait ||
            dOrient == Orientation.PortraitInverted) {
            inPortrait = true
        } else {
            inPortrait = false
        }

        console.log("device orientation changed: " + deviceOrientation)

        /* BTW, other orientations are:
        Orientation.Landscape
        Orientation.LandscapeInverted
        */
    }

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