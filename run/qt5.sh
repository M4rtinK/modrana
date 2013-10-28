#!/bin/bash
# Run modRana with the Qt5 GUI using QtQuick Controls
cd ..
# path to the main QML file
QML_MAIN="modules/gui_modules/gui_qt5/qml/main.qml"
# path to the component set
COMPONENTS="modules/gui_modules/gui_qt5/qml/universal_components/controls"

#export QML_IMPORT_DIR = /

qmlscene ${QML_MAIN} -I ${COMPONENTS}
