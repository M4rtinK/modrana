import QtQuick 2.0
import QtQuick.Controls 2.0
import "style.js" as S

Column {
    id : comboColumn
    property alias label : comboLabel.text
    property alias model : cBox.model
    property alias item : cBox.item
    property alias currentItem : cBox.currentItem
    property alias currentIndex : cBox.currentIndex
    property string description : ""
    property string translationContext : "ComboBox"
    width : parent.width

    Row {
        // no spacing if the label is empty, so that the combobox
        // can be used as a standalone label-less combobox
        spacing : comboLabel.text ? S.style.main.spacing : 0
        property var bar : S.foo
        Label {
            id : comboLabel
        }
        ComboBox {
            id : cBox
            textRole : "text"
            displayText : qsTranslate(translationContext, currentText)
            anchors.verticalCenter : comboLabel.verticalCenter
            // selected item, only assigned if user
            // clicks on an item in the context menu,
            // not if changing the current item index
            property var item
            // changes active item
            // without triggering the
            // the on current item changed signal
            property int currentItem

            property bool _skipNext : false

            onModelChanged : {
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
    }
    Label {
        text : comboColumn.description
        wrapMode : Text.Wrap
        width : parent.width
        font.italic : true
    }
}