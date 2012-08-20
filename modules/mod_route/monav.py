"""Copyright 2011  Thomas Miedema thomasmiedema@gmail.com

This file is part of MoNav.

MoNav is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

MoNav is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with MoNav.  If not, see <http://www.gnu.org/licenses/>.

Alternatively, this file may be used under the terms of the GNU
Library General Public License as published by the Free Software
Foundation; either version 2 of the License, or (at your option)
any later version.

"""
import socket
import struct

from signals_pb2 import CommandType, VersionCommand, VersionResult, RoutingCommand, RoutingResult
from signals_pb2 import Node as Waypoint


class TcpConnection(object):
    """Wrapper for socket.socket() with Google protocol buffers.

    """
    def __init__(self, host='localhost', port=8040):
        """Open a Tcp socket to host.

        # http://stackoverflow.com/questions/2038083/how-to-use-python-and-googles-protocol-buffers-to-deserialize-data-sent-over-tcp

        """
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.connect((host, port))

    def write(self, message):
        """Write a Google protocol buffers messsage to the socket.

        """
        # Writing is a 2 step process.
        # 1. an unsigned integer containing the size of the serialized message.
        # 2. the serialized message itself.
        serialized = message.SerializeToString()
        self._socket.sendall(struct.pack("I", len(serialized)))
        self._socket.sendall(serialized)
    
    def read(self, message):
        """Read and parse a Google protocol buffer message from the socket.

        (!) This function changes it's arguments.

        """
        # Read an unsigned integer containing the size of the serialized message.
        size = struct.unpack("I", self._socket.recv(struct.calcsize("I")))[0]

        # Read and parse the serialized message.
        #
        # MSG_WAITALL (since Linux 2.2)
        #
        # This flag requests that the operation block until the full 
        # request is satisfied. However, the call may still return less 
        # data than requested if a signal is caught, an error or  
        # disconnect occurs, or the next data to be received is of a 
        # different type than that returned.
        buf = self._socket.recv(size, socket.MSG_WAITALL)

        if size != len(buf):
            raise Exception('Not all bytes of message received.')

        message.ParseFromString(buf)


    def close(self):
        self._socket.close()


def get_version(connection=None):
    """Get the version of the monav daemon or server on the other side 
    of the connection.

    """
    if not connection:
        connection = TcpConnection()

    # Generate and write the command type.
    connection.write(CommandType(value=CommandType.VERSION_COMMAND))
    connection.write(VersionCommand())

    # Read result.
    result = VersionResult()
    connection.read(result)

    return result.version


def get_route(data_directory, waypoints, lookup_radius=10000, lookup_edge_names=True, connection=None):
    """Get the shortest route between a list of waypoints using MoNav.

    * connection should be a TcpConnection object.

    * data_directory should be the path to the directory called routing_
      created by the MoNav preprocessor.

    * Return type RoutingResult:
        seconds
        nodes
        edges
        edge_names
        edge_types

    * First start the monav-server.

    """
    if not connection:
        connection = TcpConnection()

    # Generate and write the command type.
    connection.write(CommandType(value=CommandType.ROUTING_COMMAND))

    # Generate the command.
    command = RoutingCommand()
    command.data_directory = data_directory
    command.lookup_radius = lookup_radius
    command.lookup_edge_names = lookup_edge_names

    if hasattr(waypoints[0], 'latitude'):
        command.waypoints.extend(waypoints)
    else:
        for latlon in waypoints:
            assert len(latlon) == 2
            waypoint = command.waypoints.add(latitude=latlon[0], longitude=latlon[1])

    # Write the command.
    connection.write(command)

    # Read result.
    result = RoutingResult()
    connection.read(result)

    # Close the connection (just in case)
    connection.close()

    if result.type == RoutingResult.SUCCESS:
        return result
    elif result.type == RoutingResult.LOAD_FAILED:
        raise Exception(str(result.type) + ": failed to load data directory")
    elif result.type == RoutingResult.LOOKUP_FAILED:
        raise Exception(str(result.type) + ": failed to lookup nearest edge")
    elif result.type == RoutingResult.ROUTE_FAILED:
        raise Exception(str(result.type) + ": failed to compute route")
    elif result.type == RoutingResult.NAME_LOOKUP_FAILED:
        raise Exception(str(result.type) + ": name lookup failed")
    elif result.type == RoutingResult.TYPE_LOOKUP_FAILED:
        raise Exception(str(result.type) + ": type lookup failed")
    else:
        raise Exception(str(result.type) + ": return value not recognized")

