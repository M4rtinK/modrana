.pragma library

var FONT_LARGE = 34;
var FONT_DEFAULT = 30;
var FONT_SMALL = 26;
var COLOR_HIGHLIGHT = "olivedrab"
var COLOR_HIGHLIGHT_TEXT = "white"
var COLOR_BACKGROUND = "#101010"
var COLOR_FONT = "lightgrey"
var COLOR_INFOLABEL = "grey"
var COLOR_DESCRIPTION = "mediumblue"
var COLOR_DESCRIPTION_NIGHT = "lightblue"
var COLOR_DIALOG_TEXT = "white"
var WIDTH_SELECTOR = 53;
var COLOR_WARNING_NIGHT = "yellow"
var COLOR_WARNING = "darkred"
var COLOR_WARNING_DARKBG = "red"

function getCacheColor(cache) {
    if (cache.found) {
        return "#80c0c0c0"
    }

    return (cache.type == 'regular' ? "chartreuse" :
            cache.type == 'multi' ? "darkorange" :
            cache.type == 'virtual' ? "blue" :
            cache.type == 'event' ? "red" :
            cache.type == 'earth' ? "darkolivegreen" :
            cache.type == 'mystery' ? "royalblue" :
            "darkslategray")
}

function getCacheColorBackground(cache) {
    return (cache.type == 'regular' ? "chartreuse" :
            cache.type == 'multi' ? "darkorange" :
            cache.type == 'virtual' ? "blue" :
            cache.type == 'event' ? "darkred" :
            cache.type == 'earth' ? "darkolivegreen" :
            cache.type == 'mystery' ? "royalblue" :
            "lightgray")
}
