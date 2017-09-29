import Sailfish.Silica 1.0

Page {
    allowedOrientations : Orientation.All
    property bool isActive : status == PageStatus.Active
    property bool isInactive : status == PageStatus.Inactive
    property bool isActivating : status == PageStatus.Activating
    property bool isDeactivating : status == PageStatus.Deactivating
}