import QtQuick 2.0
import io.thp.pyotherside 1.0

Rectangle {
    color : "green"
    width : 640
    height : 480
    Text {
        text : "hello PDB!"
    }

    Python {
        id : python
        Component.onCompleted: {
            importModule('pdb', function() {
            call('pdb.set_trace()')
            })
            }
        onError: {
            // when an exception is raised, this error handler will be called
            console.log('python error: ' + traceback);

        }
    }
}
