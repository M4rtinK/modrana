import QtQuick.Controls 1.0

MenuItem{
    signal clicked
    onTriggered : {
        clicked()
    }
}