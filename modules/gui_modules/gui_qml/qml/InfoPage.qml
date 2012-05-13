import QtQuick 1.1
import com.nokia.meego 1.0

BasePage {
    id: aboutPage
    /*
    anchors.fill : parent
    anchors.topMargin : 20
    anchors.bottomMargin : 30
    anchors.leftMargin : 30
    anchors.rightMargin : 30
    */
    headerText : "modRana"
    content {
        Label {
            id : aboutTitle
            anchors.horizontalCenter : parent.horizontalCenter
            text: "version: " + platform.modRanaVersion()
            font.pointSize: 24
        }
        Image {
            id : aboutRephoIcon
            anchors.horizontalCenter : parent.horizontalCenter
            anchors.topMargin : 10
            anchors.top : aboutTitle.bottom
            source : "image://icons/"+ rWin.theme +"/mieru.svg"
        }
        Label {
            id : aboutContactInfo
            anchors.horizontalCenter : parent.horizontalCenter
            //anchors.topMargin : 10
            anchors.top : aboutRephoIcon.bottom
            text: "<style type='text/css'>p { margin-bottom:15px; margin-top:0px; }</style>" + repho.getAboutText()

            onLinkActivated : {
                console.log('about text link clicked: ' + link)
                mainView.notify("Opening:<br><b>"+link+"</b>")
                Qt.openUrlExternally(link)
            }
        }
        Button {
            text : "Donate ?"
            anchors.horizontalCenter : parent.horizontalCenter
            anchors.topMargin : 25
            anchors.top : aboutContactInfo.bottom
            onClicked : {
                console.log('donation button clicked')
                Qt.openUrlExternally('https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=martin%2ekolman%40gmail%2ecom&lc=US&item_name=RePho%20project&currency_code=EUR&bn=PP%2dDonationsBF%3abtn_donate_LG%2egif%3aNonHosted')
            }
        }
    }
}