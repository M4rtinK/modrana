import QtQuick 2.0

Canvas {
    id: bubbleCanvas
    antialiasing: true
    // move the origin to the bubble arrow
    transformOrigin: Item.Bottom // TODO: adapt this for rightBubble ?

    property string topBubble : "topBubble"
    property string rightBubble : "rightBubble"

    property var bubbleType : bubbleCanvas.topBubble

    property bool isTopBubble : (bubbleCanvas.bubbleType == bubbleCanvas.topBubble)
    property bool isRightBubble : (bubbleCanvas.bubbleType == bubbleCanvas.rightBubble)

    property real bubbleWidth : 200
    property real bubbleHeight : 100
    property real bubbleOffset : 30

    width: isRightBubble ? bubbleWidth + bubbleOffset : bubbleWidth
    height: isTopBubble ? bubbleHeight + bubbleOffset : bubbleHeight

    property int radius: 16 * rWin.c.style.m
    property color bubbleColor: Qt.darker("grey", 1.4)

    onRadiusChanged:requestPaint()

    // Sailfish OS destroys the Canvas rendering context
    // when the application is minimised, so wee need
    // to re-render the canvas once the context is again
    // available
    onContextChanged: {
         if (bubbleCanvas.context) {
            bubbleCanvas.requestPaint()
         } else {
            return
         }
    }

    onPaint: {
        if (bubbleCanvas.bubbleType == bubbleCanvas.rightBubble) {
            paintRightBubble()
        } else {
            paintTopBubble()
        }
    }

    function paintTopBubble() {
        var ctx = getContext("2d")
        ctx.save()
        ctx.clearRect(0, 0, bubbleCanvas.width, bubbleCanvas.height);
        ctx.bubbleColor = bubbleCanvas.fillStyle
        ctx.globalAlpha = 0.6
        ctx.beginPath()
        ctx.moveTo(radius, 0)  // top side
        ctx.lineTo(bubbleWidth-radius, 0)
        // draw top right corner
        ctx.arcTo(bubbleWidth, 0, bubbleWidth, radius, radius);
        ctx.lineTo(bubbleWidth, bubbleHeight-radius)  // right side
        // draw bottom right corner
        ctx.arcTo(bubbleWidth, bubbleHeight, bubbleWidth-radius, bubbleHeight, radius);
        ctx.lineTo((bubbleWidth/2.0)+(bubbleOffset/2.75), bubbleHeight)  // bottom side right
        // bubble triangle/arrow/pointer
        ctx.lineTo(bubbleWidth/2.0, bubbleHeight+bubbleOffset)  // bottom side right
        ctx.lineTo((bubbleWidth/2.0)-(bubbleOffset/2.75), bubbleHeight)  // bottom side right
        ctx.lineTo(radius, bubbleHeight)  // bottom side left
        // draw bottom left corner
        ctx.arcTo(0, bubbleHeight, 0, bubbleHeight-radius, radius)
        ctx.lineTo(0, radius)  // left side
        // draw top left corner
        ctx.arcTo(0, 0, radius, 0, radius)
        ctx.closePath()
        ctx.fill()
        ctx.restore()
    }

    function paintRightBubble() {
        var ctx = getContext("2d")
        ctx.save()
        ctx.clearRect(0, 0, bubbleCanvas.width, bubbleCanvas.height);
        ctx.bubbleColor = bubbleCanvas.fillStyle
        ctx.globalAlpha = 0.6
        ctx.beginPath()
        ctx.moveTo(bubbleOffset+radius, 0)  // top side
        ctx.lineTo(bubbleCanvas.width-radius, 0)
        // draw top right corner
        ctx.arcTo(bubbleCanvas.width, 0, bubbleCanvas.width, radius, radius);
        ctx.lineTo(bubbleCanvas.width, bubbleHeight-radius)  // right side
        // draw bottom right corner
        ctx.arcTo(bubbleCanvas.width, bubbleHeight, bubbleCanvas.width-radius, bubbleHeight, radius);
        ctx.lineTo(bubbleOffset+radius, bubbleHeight)  // bottom side
        // draw bottom left corner
        ctx.arcTo(bubbleOffset, bubbleHeight, bubbleOffset, bubbleHeight-radius, radius)
        ctx.lineTo(bubbleOffset, (bubbleHeight/2.0)+(bubbleOffset/2.75))  // left side bottom
        // bubble triangle/arrow/pointer
        ctx.lineTo(0, bubbleHeight/2.0)  // pointy end of the pointer
        ctx.lineTo(bubbleOffset, (bubbleHeight/2.0)-(bubbleOffset/2.75))  // back to the edge
        ctx.lineTo(bubbleOffset, radius)  // left side top
        // draw top left corner
        ctx.arcTo(bubbleOffset, 0, bubbleOffset+radius, 0, radius)
        ctx.closePath()
        ctx.fill()
        ctx.restore()
    }
}