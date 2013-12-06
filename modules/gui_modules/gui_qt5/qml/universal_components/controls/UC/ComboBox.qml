import QtQuick.Controls 1.0
//
ComboBox{
    id : cBox

    // selected item, only assigned if user
    // clicks on an item in the context menu,
    // not if changing the current item index
    property variant item
    // changes active item
    // without triggering the
    // the on current item changed signal
    property int currentItem

    property bool _skipNext : false

    onModelChanged : {
        console.log("model assigned")
        _skipNext = true
    }

    onCurrentItemChanged : {
        // skip next onCurrentIndexChanged
        _skipNext = true
        currentIndex = currentItem
    }

    onCurrentIndexChanged: {
        // currentIndex is changed if a new model
        // is assigned, so we need to ignore the signal
        // once every time a new model is assigned
        if (_skipNext) {
            _skipNext = false
        } else {
            // assign selected item to the item
            // property, so that the onItemChanged
            // signal is triggered
            cBox.item = cBox.model.get(currentIndex)
        }
    }
}