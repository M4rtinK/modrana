import Sailfish.Silica 1.0

PullDownMenu {

// The popup function does nothing and is only there
// for API compatibility - the Controls TopMenu needs
// popup() to be called if used without a PageHeader
// to open the menu. So we also provide a dummy popup()
// function here with silica so that code that expects
// that TopMenu has a popup() method does not break.
function popup() {}
}