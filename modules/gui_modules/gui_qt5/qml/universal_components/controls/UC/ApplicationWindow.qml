import QtQuick.Controls 2.0
import QtQuick.Window 2.0

import "style.js" as S

ApplicationWindow {
    id : appWindow
    // report if the application wide window is in portrait
    property bool inPortrait : Screen.orientation == Qt.PortraitOrientation ||
                               Screen.orientation == Qt.InvertedPortraitOrientation

    // report if the application wide window is in an inverted orientation
    property bool inverted : Screen.orientation == Qt.InvertedPortraitOrientation ||
                             Screen.orientation == Qt.InvertedLandscape

    // The whole QtQuick Controls ApplicationWindow rotates on orientation change.
    // This is a difference from for example the Sailfish Silica ApplicationWindow,
    // where only the pages on the stack rotate, which creates some serious difficulties
    // for implementation of top level content, such as notification bubbles.
    property bool rotatesOnOrientationChange : true

    //property alias initialPage : pageStack.initialItem
    property alias pageStack : pageStack

    property int hiDPI : 0

    StackView {
        anchors.fill : parent
        id : pageStack


        onCurrentItemChanged: {
            //currentItem.forceActiveFocus()
            currentItem.focus = true
        }
    }

    function pushPage(pageInstance, pageProperties, animate) {
        // the Controls page stack disables animations when
        // false is passed as the third argument, but we want to
        // have a more logical interface, so just invert the value
        // before passing it to the page stack
        pageStack.push(pageInstance, pageProperties, !animate)
        return pageInstance
    }

    // reload the style table if the hiDPI setting is changed
    // NOTE: this should probably happen before the elements
    //       start using the style table
    onHiDPIChanged : {
        S.style = S.getStyle(appWindow.hiDPI)
    }
}