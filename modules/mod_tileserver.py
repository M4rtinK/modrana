# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# A modRana built-in tileserver
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
import random
import sys
from threading import Thread
from core.backports import six

SimpleHTTPServer = six.moves.SimpleHTTPServer
SocketServer = six.moves.socketserver

try:  # Python 2
    from urllib2 import HTTPError
except ImportError:  # Python 3
    from urllib.error import HTTPError
try:
    from  cStringIO import StringIO # python 2
except ImportError:
    from io import StringIO # python 3

from modules.base_module import RanaModule
from modules import tileserver_callback_proxy


def getModule(*args, **kwargs):
    return Tileserver(*args, **kwargs)


class Tileserver(RanaModule):
    """A modRana built-in tileserver"""

    def __init__(self, *args, **kwargs):
        RanaModule.__init__(self, *args, **kwargs)

        tileserver_callback_proxy.cb = self

        self.port = None
        self.server = None
        self.serverThread = None
        self._mapTiles = None

        if self.modrana.gui.needsLocalhostTileserver():
            self.startServer(9009)

    def firstTime(self):
        self._mapTiles = self.m.get('mapTiles', None) # mapTiles module shortcut


    def runServer(self):
        self.log.info("starting localhost tileserver")

        self.port = 9009
        #    self.tileserverPort = random.randint(8000,9000)


        #    Handler = SimpleHTTPServer.SimpleHTTPRequestHandler


        try:
            self.log.info("starting on port %d", self.port)
            self.httpd = Server(("", self.tileserverPort), self)
        except Exception:
            self.log.exception("starting server on port %d failed", self.port)
            self.port = random.randint(9000, 10000)
            self.log.info("generating random port")
            self.log.info("starting on port %d", self.port)
            self.server = Server(("", self.port), self)

        self.log.info("running at port: %d", self.port)
        self.server.serve_forever()


    def startServer(self, port):
        """
        start the tileserver
        """
        self.log.info("starting localhost tileserver")
        t = Thread(target=self.runServer)
        t.daemon = True
        t.start()
        self.serverThread = t

    def stopServer(self):
        """
        stop the tileserver
        """
        if self.server:
            self.server.socket.close()
            self.serverThread = None

    def getServerPort(self):
        """
        return the port that the tile server is currently using
        """
        return self.port

    def shutdown(self):
        self.stopServer()


class Server(SocketServer.TCPServer):
#      def __init__(self, tuple, callback):
#        SocketServer.TCPServer.init(tuple, "")
#        self.callback = callback

    class Proxy(SimpleHTTPServer.SimpleHTTPRequestHandler):
        def __init__(self, request, client_address):
            try:
                SimpleHTTPServer.SimpleHTTPRequestHandler.__init__(self, request, client_address, self)
            except:
                SimpleHTTPServer.SimpleHTTPRequestHandler.__init__(self, request, client_address, self)

        def do_GET(self):
            split = self.path.split("/")
            layer = split[1]
            z = int(split[2])
            x = int(split[3])
            y = int(split[4].split(".")[0])
            self.log.debug(self.path)
            self.log.debug(tileserver_callback_proxy.cb._mapTiles)
            try:
                tileData = tileserver_callback_proxy.cb._mapTiles.getTile(layer, z, x, y)
                if tileData:

                    self.send_response(200)
                    self.send_header("Content-type", "image/png")
                    #self.send_header("Content-type", "application/octet-stream")
                    self.send_header("Content-Length", len(tileData))
                    #              self.send_header('Server', self.version_string())
                    #              self.send_header('Date', self.date_time_string())
                    self.end_headers()

                    self.log.debug("GET returning file")

                    self.wfile.write(StringIO(tileData).read())
                    return True
                else:
                    self.log.debug("GET tile not found")
                    return False
            except HTTPError:
                e = sys.exc_info()[1]
                # forward the error code
                self.send_response(e.code)

    def finish_request(self, request, client_address):
        self.Proxy(request, client_address)
