import QtQuick.Controls 2.0

MenuItem{
    signal clicked
    onTriggered : {
        clicked()
    }
}