import QtQuick 2.0
import io.thp.pyotherside 1.0
import UC 1.0

Rectangle {
    color : "green"
    //anchors.fill : parent
    width : 640
    height : 480
    Text {
        text : "hello world"
    }

    property string guiID : "unknown"

    Python {
        id : python
        Component.onCompleted: {
            addImportPath('.');
            //importModule('pdb', function() {})
            importModule_sync('sys')
            importModule_sync('modrana')
            // fake the argv
            //call_sync('setattr','sys' , 'argv' ,'["modrana.py", "-u", "qt5", "-d", "pc"]')
            evaluate('setattr(sys, "argv" ,["modrana.py", "-u", "qt5", "-d", "pc"])')
            console.log('sys.argv faked')
            call_sync('modrana.start')
            evaluate("print('ASDASDASDASDASDASDASD')")
            evaluate("print(modrana.gui)")
            //guiID = evaluate("modrana.gui.getIDString()")
            call("modrana.gui.getIDString", [], function(result){
                guiID = result
            })
            }
        onError: {
            // when an exception is raised, this error handler will be called
            console.log('python error: ' + traceback);

        }
    }

    Button {
        text : "GUI:" + guiID
    }
}

