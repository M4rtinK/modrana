import QtQuick.Controls 1.0

ApplicationWindow {

    //property alias initialPage : pageStack.initialItem
    property alias pageStack : pageStack

    StackView {
        anchors.fill : parent
        id : pageStack
    }

    function pushPage(pageInstance, pageProperties, animate) {
        pageStack.push(pageInstance, pageProperties, animate)
    }
}