import QtQuick 2.0
import Sailfish.Media 1.0
import org.nemomobile.policy 1.0

Item {
    id : mediaKeys
    enabled : false

    signal up
    signal down

    MediaKey {
        id: mediaUp
        enabled: mediaKeysAccessResource.acquired
        key: Qt.Key_VolumeUp
        onPressed : {
            mediaKeys.up()
        }
    }
    MediaKey {
        id: mediaDown
        enabled: mediaUp.enabled
        key: Qt.Key_VolumeDown
        onPressed : {
            mediaKeys.down()
        }
    }

    Permissions {
        enabled: mediaKeys.enabled
        autoRelease: true
        // for some reason we need to be a camera or this
        // does not work - inner platform effect in action,
        // wooooo ! :D
        applicationClass: "camera"

        Resource {
            id: mediaKeysAccessResource
            type: Resource.ScaleButton
            optional: true
        }
    }
}