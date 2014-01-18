import Sailfish.Silica 1.0

Page {
    allowedOrientations : Orientation.All
    property bool isActive : status == PageStatus.Active
}