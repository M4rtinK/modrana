import QtQuick.Controls 1.0

import "style.js" as S

ApplicationWindow {
    id : appWindow
    // for now, we are in landscape when using Controls
    property bool inPortrait : appWindow.width < appWindow.height
    //property bool inPortrait : false

    //property alias initialPage : pageStack.initialItem
    property alias pageStack : pageStack

    property int hiDPI : 0

    StackView {
        anchors.fill : parent
        id : pageStack
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