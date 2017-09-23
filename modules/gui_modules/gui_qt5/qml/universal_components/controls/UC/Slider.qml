import QtQuick.Controls 2.0

Slider{
    id : slider
    property string valueText : ""
    property alias minimumValue : slider.from
    property alias maximumValue : slider.to
}