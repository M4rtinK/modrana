# -*- coding: utf-8 -*-
#---------------------------------------------------------------------------
# Handles offline routing with Monav
#---------------------------------------------------------------------------
# Copyright 2007-2008, Oliver White
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
import os
from threading import Thread
import time
import subprocess
import signal

try:
    import json
except ImportError:
    import simplejson as json

from core.singleton import modrana
from core.point import Point

RETRY_COUNT = 3 # if routing fails, try RETRY_COUNT more times
# there might be some situations where the Monav server might fail
# to return a route even if it exists - it seems to be prone to these
# errors especially at startup, even though it is possible to
# succesfully initiate a connection with it & query its version
#
# Monav routing is also very fast, so doing more tries is not a problem


import logging
log = logging.getLogger("mod.routing.monav_support")

# Marble stores monav data like this on the N900:
# /home/user/MyDocs/.local/share/marble/maps/earth/monav/motorcar/europe/czech_republic

class MonavBase(object):
    def __init__(self, data_path):
        self._data_path = data_path

    @property
    def data_path(self):
        return self._data_path

    @data_path.setter
    def data_path(self, value):
        self._data_path = value

    def get_monav_directions(self, waypoints, route_params):
        """Get route from Monav for a list of waypoints

        :param list waypoints: a list of waypoints (Point objects)
        :return: routing result object or None if routing failed
        :rtype: routing result object or None
        TODO: verify this
        """

class MonavServer(MonavBase):
    """This class represents the Monav routing server,
       which is a part of the full Monav "suite".
       The Monav routing server provides offline routing services over a TCP connection
       serialised in protocol buffers.
       As the Monav upstream project is dead, so is the Monav routing server and it is
       even hard to just compile it these days. As a result this class is basically
       useful only on the N900, for which a working Monav routing server binary exists.
       For more up-to-date platforms (supporting Qt 5) the Monav Light routing utility
       should be used instead.
    """
    def __init__(self, monav_data_path, monav_server_executable_path):
        MonavBase.__init__(self, data_path=monav_data_path)
        self._monav_server_process = None
        self._monav_server_binary_path = monav_server_executable_path
        # make return codes easily accessible
        from signals_pb2 import RoutingResult
        self._return_codes = RoutingResult

        # connect to the shutdown signal so that we can stop
        # the server when modRana shuts down
        modrana.shutdown_signal.connect(self.stop_server)

    def start_server(self, port=None):
        log.info('starting Monav server')
        started = False

        # only import Monav server & company when actually needed
        # -> the protobuf modules are quite large
        import monav_server

        try:
            # first check if monav server is already running
            try:
                monav_server.TcpConnection()
                log.error('server already running')
            except Exception:
                import sys

                if not self._monav_server_binary_path:
                    log.error("can't start monav server - monav server binary missing")
                    return
                log.info('using monav server binary in:\n%s', self._monav_server_binary_path)

                def _start_server_process(self):
                    self._monav_server_process = subprocess.Popen(
                        "%s" % self._monav_server_binary_path
                    )

                t = Thread(target=_start_server_process, args=[self], name='asynchronous monav-server start')
                t.setDaemon(True) # we need that the thread dies with the program
                t.start()
                timeout = 5 # in s
                sleepTime = 0.1 # in s
                startTimestamp = time.time()
                elapsed = 0
                # wait up to timeout seconds for the server to start
                # and then return
                while elapsed < timeout:
                    if self._monav_server_process:
                        try:
                            # test if the server is up and accepting connections
                            monav_server.TcpConnection()
                            break
                        except Exception:
                            pass # not yet fully started
                    time.sleep(sleepTime)
                    elapsed = time.time() - startTimestamp
                started = True
                # TODO: use other port than 8040 ?, check out tileserver code
        except Exception:
            log.exception('starting Monav server failed')

        if started:
            log.info('Monav server started')

    def stop_server(self):
        log.info('stopping Monav server')
        stopped = False
        try:
            if self._monav_server_process:
                # Python 2.5 doesn't have POpen.terminate(),
                # so we use this
                os.kill(self._monav_server_process.pid, signal.SIGKILL)
                stopped = True
            else:
                log.error('no Monav server process found')
        except Exception:
            log.exception('stopping Monav server failed')
        self._monav_server_process = None
        if stopped:
            log.info('Monav server stopped')

    @property
    def server_running(self):
        if self._monav_server_process:
            return True
        else:
            return False

    def get_monav_directions(self, waypoints, route_params):
        """Search for a route using Monav routing server"""
        # check if Monav server is running

        if self.data_path is None:
            log.error("error, data_path not set (is None)")
            return None
        if not self.server_running:
            self.start_server() # start the server

        # Monav works with (lat, lon) tuples so we
        # need to convert the waypoints to a list of
        # (lat,lon) tuples
        waypoints = [x.getLL() for x in waypoints]

        # only import Monav server & company when actually needed
        # -> the protobuf modules are quite large
        import monav_server

        log.info('monav server: starting route search')
        start = time.clock()
        tryNr = 0
        result = None
        while tryNr < RETRY_COUNT:
            tryNr += 1
            try:
                result = monav_server.get_route(self.data_path, waypoints)
                break
            except Exception:
                log.exception('routing failed')

                if tryNr < RETRY_COUNT:
                    log.info('retrying')
        if tryNr < RETRY_COUNT:
            log.info('monav server: search finished in %1.2f ms and %d tries', 1000 * (time.clock() - start), tryNr)
            return result
        else:
            log.error('monav server: search failed after %d retries', tryNr)
            return None


class Edge(object):
    def __init__(self, edge_list):
        self._edge_list = edge_list

    @property
    def n_segments(self):
        return self._edge_list[0]

    @property
    def name_id(self):
        return self._edge_list[1]

    @property
    def type_id(self):
        return self._edge_list[1]

    @property
    def seconds(self):
        return self._edge_list[3]

    @property
    def branching_possible(self):
        return  self._edge_list[4]


class MonavLightResult(object):

    SUCCESS = "SUCCESS"
    LOAD_FAILED = "LOAD_FAILED"
    SOURCE_LOOKUP_FAILED = "SOURCE_LOOKUP_FAILED"
    TARGET_LOOKUP_FAILED = "TARGET_LOOKUP_FAILED"
    ROUTE_FAILED = "ROUTE_FAILED"

    def __init__(self, result_dict):
        self._result_dict = result_dict
        self._nodes = None
        self._edges = None

    @property
    def type(self):
        return self._result_dict["status"]

    def status_message(self):
        return self._result_dict["statusMessage"]

    @property
    def nodes(self):
        if self._nodes is None:
            node_points = []
            for node in self._result_dict["nodes"]:
                node_points.append(Point(lat=node[0], lon=node[1]))
                self._nodes = node_points
        return self._nodes

    @property
    def edges(self):
        if self._edges is None:
            edges = []
            for edge in self._result_dict["edges"]:
                edges.append(Edge(edge_list=edge))
            self._edges = edges
        return self._edges

    @property
    def edge_names(self):
        return self._result_dict["edgeNames"]

    @property
    def edge_types(self):
        return self._result_dict["edgeTypes"]

    @property
    def seconds(self):
        return  self._result_dict["seconds"]

class MonavLight(MonavBase):
    """This class represents the Monav Light routing utility"""

    def __init__(self, monav_data_path, monav_light_executable_path):
        MonavBase.__init__(self, data_path=monav_data_path)
        self._monav_light_executable_path = monav_light_executable_path

    def _get_input_json(self, waypoints, route_params):
        point_list = []
        for point in waypoints:
            point_list.append([point.lat, point.lon, 0, 0])

        # the last two fields in the list representing a Monav waypoint
        # are heading penalty (penalty in meters for edge with direction
        # opposite of heading) and heading (degrees from North)
        # TODO: support heading/heading penalty ?
        return json.dumps({
            "dataDirectory" : self.data_path,
            "lookupEdgeNames" : True,
            "routingRadius" : 10000,
            "waypoints" : point_list
        })

    def get_monav_directions(self, waypoints, route_params):
        start = time.clock()
        input_json = self._get_input_json(waypoints, route_params)
        log.info('monav light: starting route search')
        process = subprocess.Popen([self._monav_light_executable_path, input_json], stdout=subprocess.PIPE)
        stdout, stderr = process.communicate()
        if process.returncode == 0:
            # Monav Light outputs the route as JSON to stdout
            result_dict = json.loads(stdout.decode("utf-8"))
            result = MonavLightResult(result_dict)
            if result.type == result.SUCCESS:
                log.info('monav light: route search successful (%1.2f ms)', 1000 * (time.clock() - start))
            else:
                log.error("monav light: routing failed: %s", result.status_message())
            return result
        else:
            log.error("calling monav-light failed with return code %d", process.returncode)
