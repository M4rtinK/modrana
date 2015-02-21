//OptProp.qml (OptionsProperty)
import QtQuick 2.0

Item {
    id : optProp
    property string key : ""
    property var value : null
    property bool initialized : false

    // if the value changes, save it to the persistent options
    // dictionary - but only once we are initialized
    // (this should prevent use from overwriting the given key
    //  by the default value)
    onValueChanged : {
        if (optProp.initialized && optProp.key) {
            rWin.set(optProp.key, optProp.value)
        }
    }

    // once the key is set (this also happens when a key value is
    // provided when the object ins instantiated) fetch the value
    // from the persistent options dictionary and report that
    // we are ready once done
    onKeyChanged : {
        optProp.initialized = false
        rWin.get(optProp.key, optProp.value, function(v){
            optProp.value = v
            optProp.initialized = true
        })
    }
}