import QtQuick 1.1
import com.nokia.meego 1.0
import "uiconstants.js" as UI


Page {
    id: listPage
    tools: commonTools
    orientationLock: PageOrientation.LockPortrait

    function showDetailsPage(page) {
        tabGroup.currentTab.push(page)
    }

    function showAndResetDetailsPage() {
        while (tabDetailsPageStack.depth > 1) {
            tabDetailsPageStack.pop()
        }
        tabGroup.currentTab = tabDetailsPageStack
    }
    
    function showSettings() {
        pageSettings.source = "SettingsPage.qml";
        rootWindow.pageStack.push(pageSettings.item);
    }
    
    function showCamera() {
        pageCamera.source = "VideoPage.qml";
        rootWindow.pageStack.push(pageCamera.item);
    }


    TabGroup {
        id: tabGroup
        currentTab: tabCompass
        CompassPage {
            id: tabCompass
        }

        MapPage {
            id: tabMap
        }

        PageStack {
            id: tabDetailsPageStack
            anchors.fill: parent
            Component.onCompleted: {
                push(pageDetailsDefault)
            }

            function openMenu() {
                if (currentPage.openMenu) {
                    currentPage.openMenu();
                } else {
                    pageDetailsDefault.openMenu()
                }

            }

        }

        PageStack {
            id: tabListPageStack
            anchors.fill: parent
            Component.onCompleted: {
                push(pageList)
            }

            function openMenu() {
                if (currentPage.openMenu) {
                    currentPage.openMenu();
                } else {
                    pageList.openMenu()
                }
            }

        }
    }
}
