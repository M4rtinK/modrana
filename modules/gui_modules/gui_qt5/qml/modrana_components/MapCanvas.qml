//MapCanvas.qml
//
// A wrapper for the canvas element that adds some map-drawing specific functionality.

import QtQuick 2.0

Canvas {
    id: canvas
    visible: true

    property var pinchmap : null

    onVisibleChanged : {
        if (canvas.visible) {
            canvas.requestFullPaint()
        }
    }

    property var paintStart : new Date().valueOf()

    property bool clearCanvas : true

    signal fullPaint(var ctx)
    signal retainedPaint(var ctx)

    function requestFullPaint() {
        clearCanvas = true
        requestPaint()
    }

    function requestRetainedPaint() {
        clearCanvas = false
        requestPaint()
    }

    onPaint : {
        paintStart = new Date().valueOf()
        var ctx = canvas.getContext("2d")
        ctx.save()
        if (clearCanvas) {
            // clear the canvas
            ctx.clearRect(0,0,canvas.width,canvas.height)
            ctx.translate(pinchmap.width, pinchmap.height)
            fullPaint(ctx)
        } else {
            ctx.translate(pinchmap.width, pinchmap.height)
            retainedPaint(ctx)
        }
        // Why the translate() ?
        //
        // The canvas has its x,y coordinates shifted to the upper left, so that
        // when it is moved during map panning, the offscreen parts of the route will
        // be visible and not cut off. Because of this we need to apply a translation
        // before we start drawing the route and related objects to take the shifted
        // origin into account.
        ctx.restore()
        // restore the clearCanvas property back to initial state
        clearCanvas = false
        // print canvas redraw time if requested
        if (rWin.pinchmapCanvasDebug) {
            rWin.log.debug(pinchmap.name + ": canvas redraw time: " + (new Date().valueOf() - paintStart) + " ms")
        }
    }

    Connections {
            target: canvas.visible ? pinchmap : null
            onCenterSet: {
                canvas.requestFullPaint()
            }
            onZoomLevelChanged: {
                canvas.requestFullPaint()
            }
            onMapPanEnd: {
                canvas.requestFullPaint()
            }
    }
}
