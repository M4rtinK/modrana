// Wrap independent Pages with platform specific Page object

var prefix = 'import QtQuick 1.1; import "../ic";'

function loadPage(pageName, parent) {
    var wrappedPage = prefix + pageName +"{}"
    //console.log("wrapping: " + wrappedPage)
    return Qt.createQmlObject(wrappedPage, parent)
}

/*
// this might be useful again in some environment where the built-in
// page implementation might not work

var prefix = 'import QtQuick 1.1; import com.nokia.meego 1.0; import "../ic";  Page {'

function loadPage(pageName, parent) {
    var wrappedPage = prefix + pageName +"{} }"
    console.log("wrapping: " + wrappedPage)
    return Qt.createQmlObject(wrappedPage, parent)
}
*/