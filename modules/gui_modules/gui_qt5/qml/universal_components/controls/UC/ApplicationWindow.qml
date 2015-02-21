import QtQuick.Controls 1.0

ApplicationWindow {
    id : appWindow
    // for now, we are in landscape when using Controls
    property bool inPortrait : appWindow.width < appWindow.height
    //property bool inPortrait : false

    //property alias initialPage : pageStack.initialItem
    property alias pageStack : pageStack

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
}