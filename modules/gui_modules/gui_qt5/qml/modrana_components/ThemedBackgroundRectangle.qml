// ThemedBackgroundRectangle.qml
// A background rectangle that respects the modRana theme.
import UC 1.0

BackgroundRectangle {
    id : br
    normalColor : rWin.theme.color.main_fill
    cornerRadius : rWin.isDesktop ? 0 : rWin.c.style.listView.cornerRadius
}
