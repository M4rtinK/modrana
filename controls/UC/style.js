.pragma library

var hiDPI = 0
var style = getStyle(hiDPI)

function getStyle(i) {
    return {
        "m" : [1, 2][i], // approximate size multiplier
        "main" : {
            "multiplier" : [1, 2][i],
            "spacing" : [8, 16][i],
            "spacingBig" : [16, 32][i]
        },
        "dialog" : {
            "item" : {
                "height" : [80, 160][i]
            }
        },
        "listView" : {
            "spacing" : [8, 16][i],
            "cornerRadius" : [8, 16][i],
            "itemBorder" : [20, 40][i],
        }
    }
}
