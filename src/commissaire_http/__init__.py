#!/usr/bin/env python3
# Copyright (C) 2016  Red Hat, Inc
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
"""
Prototype http server.
"""

import logging

from wsgiref.simple_server import WSGIServer, make_server
from socketserver import ThreadingMixIn


class ThreadedWSGIServer(ThreadingMixIn, WSGIServer):
    """
    Threaded version of the WSIServer
    """
    pass


class CommissaireHttpServer:
    """
    Http Server for Commissaire.
    """

    logger = logging.getLogger('CommissaireHttpServer')

    def __init__(self, bind_host, bind_port, dispatcher, tls_pem_file=None):
        """
        Initializes a new CommissaireHttpServer instance.
        """
        self._bind_host = bind_host
        self._bind_port = bind_port
        self._tls_pem_file = tls_pem_file
        self._httpd = make_server(
            self._bind_host,
            self._bind_port,
            dispatcher.dispatch,
            server_class=ThreadedWSGIServer)
        # If we are given a PEM file then wrap the socket
        if tls_pem_file:
            import ssl
            self._httpd.socket = ssl.wrap_socket(
                self._httpd.socket,
                certfile=self._tls_pem_file,
                ssl_version=ssl.PROTOCOL_TLSv1_2,
                server_side=True)
            self.logger.info('Using TLS with {}'.format(self._tls_pem_file))

        self.logger.debug('Created httpd server: {}:{}'.format(
            self._bind_host, self._bind_port))

    def serve_forever(self):
        """
        Serve HTTP.
        """
        try:
            self._httpd.serve_forever()
        except Exception as error:
            self.logger.error('Server shut down {}: {}'.format(
                type(error), error))
