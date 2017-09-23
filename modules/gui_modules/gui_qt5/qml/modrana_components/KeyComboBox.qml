//KeyComboBox.qml
//
// ModRana uses an persistent dictionary
// to configure a lot of stuff, so there will
// be a lot of comboboxes in options, most of them
// mapped on a key in the persistent dict & it's
// current value.
// KeyComboBox makes it possible to just assign the
// key property and the combobox will asynchronously
// fetch the value if the key from Python,
// go over all ListElements in the ListModel and set
// itemIndex based on the index of the found element.
// If no element is found, currentIndex is set to null
// Also, if setValue is true, set the persistent dictionary
// key to the value of the clicked item.
//
// NOTE: The the ListItems used need to have an attribute
//       named "value" for both these features to work.

import QtQuick 2.0
import UC 1.0

ComboBox {
    property string key
    property string value
    property var defaultValue
    property bool setValue : true

    id : keyCombo

    onKeyChanged : {
        // asynchronously set initial value based
        // on the modRana persistent dictionary
        // value
        // TODO: skip the for loop if no key is found ?
        // (will probably need something like get_exists
        // function in GUI module & rWin, that only runs the callback
        // if the key exists in the dictionary)
        rWin.get(keyCombo.key, keyCombo.defaultValue, function(value) {
            var foundMatch = false
            for(var i = 0; keyCombo.model.count; i++) {
                // check if the element has the
                // value we got from the persistent dict
                if (keyCombo.model.get(i).value == value) {
                    // matching value found, set index & return
                    keyCombo.currentIndex = i
                    keyCombo.value = value
                    foundMatch = true
                    break
                    return
                }
            }
            // we went over all elements without finding a match,
            // set currentIndex to null
            if (!foundMatch) {
                keyCombo.currentIndex = -1
            }
        })
    }

    onItemChanged : {
        if (keyCombo.setValue && keyCombo.key && item) {
            // set the value of the persistent dictionary key
            // to the value of the selected item
            rWin.set(keyCombo.key, item.value)
            keyCombo.value = item.value
        }
    }
}