//ThemedListView.qml
//
// A list view respecting Tsubame styles, themes
// and default settings.
// Main aim - have the stuff here so it does not have
// to be filled again foe each instance.

import QtQuick 2.0
import UC 1.0

PlatformListView {
    spacing : rWin.isDesktop ? rWin.c.style.listView.spacing/4 : rWin.c.style.listView.spacing
    clip : true
    VerticalScrollDecorator {}
}

