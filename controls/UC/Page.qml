import QtQuick 2.0
import QtQuick.Controls 2.0

Page {
    property bool isActive : StackView.status == StackView.Active
    property bool isInactive : StackView.status == StackView.Inactive
    property bool isActivating : StackView.status == StackView.Activating
    property bool isDeactivating : StackView.status == StackView.Deactivating
}