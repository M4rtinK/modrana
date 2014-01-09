import Sailfish.Silica 1.0
ApplicationWindow{
    property bool inPortrait : _setOrientation(deviceOrientation)

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
    property variant visibility : 5

    function pushPage(pageInstance, pageProperties, animate) {
        var animateFlag
        if (animate) {
            animateFlag = PageStackAction.Animated
        } else {
            animateFlag = PageStackAction.Immediate
        }
        pageStack.push(pageInstance, pageProperties, animateFlag)

    }
}