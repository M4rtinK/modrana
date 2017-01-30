//KeyComboBox.qml
//
// ModRana uses an persistent dictionary
// to configure a lot of stuff and there is a lot
// of text switches comboboxes in options, most of them
// mapped on a key in the persistent dict & it's
// current value.
// KeyTextSwitch makes it possible to just assign the
// key property and the text switch will asynchronously
// fetch the value of the key from Python and set the
// checked property automatically.

import QtQuick 2.0
import UC 1.0

TextSwitch {
    property string key
    property bool defaultValue : null
    property bool checkedValid : true

    id : keyTextSwitch

    onKeyChanged : {
        // asynchronously set initial value based
        // on the modRana persistent dictionary
        // value
        if (keyTextSwitch.defaultValue == null) {
            rWin.log.warning("KeyTextSwitch for " + keyTextSwitch.key + " has no default value")
        }
        rWin.get(keyTextSwitch.key, keyTextSwitch.defaultValue, function(value) {
            checkedValid = false
            if (value) {
                keyTextSwitch.checked = true
            } else {
                keyTextSwitch.checked = false
            }
            checkedValid = true
        })
    }

    onCheckedChanged : {
        if (keyTextSwitch.key) {
            // set the value of the persistent dictionary key
            // to the value of the selected item
            rWin.set(keyTextSwitch.key, keyTextSwitch.checked)
        }
    }
}