#!/bin/bash
# Run modRana with the Qt5 GUI using QtQuick Controls
cd ..
# path to the main QML file
QML_MAIN="modules/gui_modules/gui_qt5/qml/main.qml"
# path to the component set
COMPONENTS="modules/gui_modules/gui_qt5/qml/universal_components/controls"

#export QML_IMPORT_DIR = /

CURRENT_LANG=$(locale | grep LANG | cut -d= -f2 | cut -d. -f1)

qmlscene-qt5 --verbose --translation translations/harbour-modrana-${CURRENT_LANG}.qm ${QML_MAIN} -I ${COMPONENTS}
