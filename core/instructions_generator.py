# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# A turn by turn instructions generator
#----------------------------------------------------------------------------
# Copyright 2012, Martin Kolman
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#---------------------------------------------------------------------------

from core import geo
from core.point import TurnByTurnPoint

from core.i18n import _

TURN_SLIGHTLY_LEFT = 7
TURN_LEFT = 6
TURN_SHARPLY_LEFT = 5
MAKE_A_U_TURN = 4
TURN_SHARPLY_RIGHT = 3
TURN_RIGHT = 2
TURN_SLIGHTLY_RIGHT = 1
HEAD_STRAIGHTFORWARD = 0

UNKNOWN_TURN_TYPE_MESSAGE = "you might need to turn left or right"

turnTypes = {
    TURN_SLIGHTLY_LEFT: _("turn slightly left"),
    TURN_LEFT: _("turn left"),
    TURN_SHARPLY_LEFT: _("turn sharply left"),
    MAKE_A_U_TURN: _("make a U-turn"),
    TURN_SHARPLY_RIGHT: _("turn sharply right"),
    TURN_RIGHT: _("turn right"),
    TURN_SLIGHTLY_RIGHT: _("turn slightly right"),
    HEAD_STRAIGHTFORWARD: _("head straightforward")
}


def _get_turn_message(turnType):
    return turnTypes.get(turnType, UNKNOWN_TURN_TYPE_MESSAGE)


def detect_monav_turns(result):
    """Go through the edges and try to detect turns,
       return a list of RoutingPoints for the turns.

       :param result: a Monav offline routing result
       :type result: Monav offline routing result object
       :returns: list of RoutingPoints for turns
       :rtype: list of RoutingPoint instances
    """

    # How to get the corresponding nodes for edges
    # -> edges are ordered and contain the n_segments property
    # -> n_segments describes from how many segments the given edge consists
    # -> by counting n_segments for subsequent edges, we get the node id
    # EXAMPLE:
    # a route with 2 edges, 3 segments each
    # -> firs point has id 0
    # -> the last point od the first edge has id 3
    # -> the last point of the route has id 6

    turns = []

    edges = result.edges
    nodes = result.nodes
    names = result.edge_names

    # need at least two edges for any meaningful routing
    if len(edges) >= 2:
        lastEdge = edges[0]

        nodeId = 0
        maxNodeId = len(nodes) - 1
        for edge in edges[1:]:
            nodeId += lastEdge.n_segments
            edgeId = edge.type_id
            nameId = edge.name_id
            name = names[nameId]

            #      if lastEdge.branching_possible:
            if True: # looks like branching possible is not needed
                # turn directions are actually needed only
                # when there are some other roads to to turn to
                lastName = names[lastEdge.name_id]
                if lastEdge.type_id != edgeId or lastName != name:
                    # if route type or name changes, it might be a turn
                    node = nodes[nodeId]
                    if nodeId <= maxNodeId:
                        prevNode = nodes[nodeId - 1]
                        nextNode = nodes[nodeId + 1]
                        # NOTE: if the turn consists
                        # from many segments, taking more points into
                        # account might be needed
                        first = prevNode.latitude, prevNode.longitude
                        middle = node.latitude, node.longitude
                        last = nextNode.latitude, nextNode.longitude
                        angle = geo.turn_angle(first, middle, last)

                        turnDescription = _get_turn_description(angle, name=name)
                        # get the corresponding node

                        turns.append(TurnByTurnPoint(node.latitude, node.longitude, message=turnDescription))
                        # DEBUG
                        # turns.append(TurnByTurnPoint(prevNode.latitude, prevNode.longitude, message="prev"))
                        # turns.append(TurnByTurnPoint(nextNode.latitude, nextNode.longitude, message="next"))

            lastEdge = edge
    return turns

def _get_turn_description(angle, name=None):
    """generate turn description based on the turn angle and
    append street name, if known"""
    if 8 < angle <= 45:
        turnType = TURN_SLIGHTLY_LEFT
    elif 45 < angle <= 135:
        turnType = TURN_LEFT
    elif 135 < angle <= 172:
        turnType = TURN_SHARPLY_LEFT
    elif 172 < angle <= 188:
        turnType = MAKE_A_U_TURN
    elif 188 < angle <= 225:
        turnType = TURN_SHARPLY_RIGHT
    elif 225 < angle <= 315:
        turnType = TURN_RIGHT
    elif 315 < angle <= 352:
        turnType = TURN_SLIGHTLY_RIGHT
    else: # 352 < angle <= 8
        turnType = HEAD_STRAIGHTFORWARD
        # get the basic turn message
    message = _get_turn_message(turnType)
    if name:
        # append street name
        message = "%s to %s" % (message, name)
    return message