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

    DetailsDefaultPage {
        id: pageDetailsDefault
    }

    ListPage {
        id: pageList
    }
    
    Loader {
        id: pageSettings
    }


    ToolBarLayout {
        id: commonTools
        visible: true
        ToolIcon {
            iconId: "toolbar-back" + ((! tabGroup.currentTab.depth || tabGroup.currentTab.depth < 2) ? "-dimmed" : "")// + (theme.inverted ? "-white" : "")
            onClicked: {
                if (tabGroup.currentTab.depth && tabGroup.currentTab.depth > 1) tabGroup.currentTab.pop();
            }

        }

        ButtonRow {
            style: TabButtonStyle { }
            TabButton {
                //text: "Compass"
                iconSource: "../data/icon-m-toolbar-compass" + (theme.inverted ? "-night" : "") + ".png"
                tab: tabCompass
            }
            TabButton {
                //text: "Map"
                iconSource: "../data/icon-m-toolbar-map" + (theme.inverted ? "-night" : "") + ".png"
                tab: tabMap
            }
            TabButton {
                //text: "Details"
                tab: tabDetailsPageStack
                iconSource: "image://theme/icon-m-toolbar-new-message" + (theme.inverted ? "-white" : "")
            }
            TabButton {
                //text: "Details"
                tab: tabListPageStack
                iconSource: "image://theme/icon-m-toolbar-search" + (theme.inverted ? "-white" : "")
            }
        }


        ToolIcon {
            iconId: "toolbar-view-menu"
            onClicked: {
                tabGroup.currentTab.openMenu();
            }

        }
    }
    
}
