// LocationSource.qml
// Qt5 position source control
// NOTE: This is in a separate QML file,
//       so that it can be imported dynamically
//       at runtime to check it positioning is
//       available on the given platform / Qt5 version.
//       If the import fails, a fake dummy source is used.

import QtPositioning 5.2
PositionSource {
    id: locSource
    updateInterval: 1000
}
