import QtQuick.Controls 1.0

ApplicationWindow {

property alias initialPage : pageStack.initialItem

StackView {
    id : pageStack
}
}