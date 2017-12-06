import QtQuick 2.0
import Sailfish.Silica 1.0

ComboBox {
    id : cBox
    labelMargin : 0
    // selected item, only assigned if user
    // clicks on an item in the context menu,
    // not if changing the current item index
    property var item
    property string translationContext : "ComboBox"

    menu : ContextMenu {
        id : cMenu
        Repeater {
            id : cRepeater
            model : cBox.model
            MenuItem {
                text : qsTranslate(translationContext, model.text)
                onClicked : {
                    cBox.currentItem = model
                }
            }
        }
    }
    property var model
    // how does this work ?
    //
    // Menu items are added with a ListModel to the
    // model property, which dynamically adds them to the
    // context menu. Once an item is clicked, its underlying
    // ListElement is returned so onCurrentItemChanged
    // is triggered.

    onCurrentIndexChanged: {
            // assign selected item to the item
            // property, so that the onItemChanged
            // signal is triggered
            cBox.item = cBox.model.get(currentIndex)
    }
}