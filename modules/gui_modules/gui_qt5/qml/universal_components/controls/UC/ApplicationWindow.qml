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
        pageStack.push(pageInstance, pageProperties, animate)
        return pageInstance
    }
}