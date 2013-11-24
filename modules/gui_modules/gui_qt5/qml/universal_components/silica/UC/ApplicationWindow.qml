import Sailfish.Silica 1.0
ApplicationWindow{
    // the Silica ApplicationWindow
    // does not inherit the Window element,
    // so we need to add some properties
    // for a common API with Controls
    property string title
    property variant visibility : 5
}