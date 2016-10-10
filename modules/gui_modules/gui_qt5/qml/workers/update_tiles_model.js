WorkerScript.onMessage = function(message) {
    // Update the tiles data model to the given corner tile x/y,
    // and horizontal/vertical tile number.
    // This basically amounts to newly enumerating the tiles
    // while keeping items already in the lists so that the corresponding
    // delegates are not needlessly re-rendered.

    var cornerX = message.cornerX
    var cornerY = message.cornerY
    var tilesX = message.tilesX
    var tilesY = message.tilesY

    var maxCornerX = cornerX + tilesX - 1
    var maxCornerY = cornerY + tilesY - 1

    /*
    console.log("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    console.log("UPDATE TILES MODEL")
    console.log("COUNT: " + message.tilesModel.count)
    console.log("cornerX: " + cornerX)
    console.log("cornerY: " + cornerY)
    console.log("tilesX: " + tilesX)
    console.log("tilesY: " + tilesY)
    console.log("maxCornerX: " + maxCornerX)
    console.log("maxCornerY: " + maxCornerY)
    console.log("INITIAL COUNT: " + message.tilesModel.count)
    */

    // tiles that should be on the screen due to the new coordinate update
    var newScreenContent = {}
    // tiles that need to be added (eq. were not displayed before the coordinate
    // were updated)
    var newTiles = []
    // find what new tiles are needed
    //var newSCCount = 0
    //var newTilesCount = 0
    for (var cx = cornerX; cx<=maxCornerX; cx++) {
        for (var cy = cornerY; cy<=maxCornerY; cy++) {
            var tileId = cx + "/" + cy
            newScreenContent[tileId] = true
            //newSCCount++
            if (!(tileId in message.shouldBeOnScreen)) {
                // this a new tile that was not on screen before the coordinate update
                newTiles.push({"x" : cx, "y" : cy, "id" : tileId})
                //newTilesCount++
            }
        }
    }

    // update the pinchmap-wide "what should be on screen" dict
    message.shouldBeOnScreen = newScreenContent

    // go over all tiles in the tilesModel list model that is used to generate the tile delegates
    // - if the tile is in newScreenContent do nothing - the tile is still visible
    // - if the tile is not in newScreenContent it should no longer be visible, there are two options in this case:
    //   1) if newTiles is non-empty, pop a tile from it and reset coordinates for the tile, effectively reusing
    //      the tile item & it's delegate instead of destroying it and creating a new one
    //   2) if newTiles is empty just remove the item, which also destroys the delegate

    //var iterations = 0
    //var removed = 0
    //var recycledCount = 0

    for (var i=0;i<message.tilesModel.count;i++){
        //iterations++
        var tile = message.tilesModel.get(i)
        if (tile != null) {
            if (!(tile.tile_coords.id in newScreenContent)) {
                // check if we can recycle this tile by recycling it into one
                // of the new tiles that should be displayed
                var newTile = newTiles.pop()
                //console.log("RECYCLING: " + tile.tile_coords.id + " to " + newTile.id)
                if (newTile) {
                    //recycledCount++
                    // recycle the tile by setting the coordinates to values for a new tile
                    message.tilesModel.set(i, {"tile_coords" : newTile})
                } else {
                    // no tiles to recycle into, so just remove the tile
                    message.tilesModel.remove(i)
                    i--
                    //console.log("REMOVING: " + tile.tile_coords)
                    //removed++
                }
            }
        }
    }

    // Add any items remaining in newTiles to the tilesModel, this usually means:
    // - this is the first run and the tilesModel is empty
    // - the viewport has been enlarged and more tiles in total are now visible than before
    // If no new tiles are added to the tilesMode, it usually means that the viewport is the
    // same (all tiles are recycled) or has even been shrunk.
    //var tilesAdded = 0
    for (var i=0; i < newTiles.length; i++){
        newTile = newTiles[i]
        message.tilesModel.append({"tile_coords" : newTile})
        //tilesAdded++
    }

    // send the changes to the tiles model in the main QML context by
    // synchronizing the local version of the tiles model
    message.tilesModel.sync()
    // notify the main QML context that we are done
    WorkerScript.sendMessage({shouldBeOnScreen : message.shouldBeOnScreen})

    /*
    console.log("NEW SCREEN CONTENT: " + newSCCount)
    console.log("NEW TILES: " + newTilesCount)
    console.log("ITERATIONS: " + iterations)
    console.log("REMOVED: " + removed)
    console.log("RECYCLED: " + recycledCount)
    console.log("ADDED: " + tilesAdded)
    console.log("UPDATE TILES MODEL DONE")
    console.log("TILE MODEL COUNT: " + message.tilesModel.count)
    console.log("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    */
}
