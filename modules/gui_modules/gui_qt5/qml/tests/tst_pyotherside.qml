import QtQuick 2.0
import QtTest 1.2
import "../functions.js" as F
import io.thp.pyotherside 1.4

TestCase {
    id : pTest
    name: "Test if PyOtherSide appears to be working."

    property bool errorHappened : false
    property bool signalReceived : false
    property var signalValue : null

    Python {
        id : python
        onError: {
            pTest.errorHappened = true
        }
        onReceived : {
            pTest.signalReceived = true
            pTest.signalValue = data
        }
    }

    function test_evaluate() {
        compare(python.evaluate("1 + 2"), 3)
        compare(python.evaluate('"a%s" % "bc"'), "abc")
        compare(python.evaluate(''), undefined)
    }

    function test_sync() {
        // tests synchronous imports and calls
        compare(pTest.signalReceived, false)
        compare(pTest.signalValue, null)

        python.importModule_sync('pyotherside');
        python.call_sync('pyotherside.send', ['hello world!', 123]);

        compare(pTest.signalReceived, true)
        compare(pTest.signalValue, ['hello world!', 123])

    }

    function test_error() {
        // test PyOtherSide error reporting
        compare(pTest.errorHappened, false)
        // raise an error
        python.importModule_sync('thismoduledoesnotexisthopefully')
        python.evaluate('[ 123 [.syntax234-error!')
        compare(pTest.errorHappened, true)

    }
}
