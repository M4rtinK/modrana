import QtQuick 2.0
import QtQuick.Controls 2.0

Menu {
    x : parent.width - width
    modal : true
    function popup() {
        open()
    }
}