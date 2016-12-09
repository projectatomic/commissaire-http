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
Main Commissaire application server code.
"""

import logging

from argparse import Namespace
from socketserver import ThreadingMixIn
from wsgiref.simple_server import WSGIServer, WSGIRequestHandler, make_server

from commissaire.util.config import read_config_file
from commissaire_http.bus import Bus
from commissaire_http.util.cli import parse_to_struct


def parse_args(parser):
    """
    Parses and combines arguments from the server configuration file
    and the command-line invocation.  Command-line arguments override
    the configuration file.

    The 'parser' argument should be a fresh argparse.ArgumentParser
    instance with a suitable description, epilog, etc.  This method
    will add arguments to it.

    :param parser: An argument parser instance
    :type parser: argparse.ArgumentParser
    :returns: The parsed arguments in the form of a Namespace
    :rtype: argparse.Namespace
    """
    # Do not use required=True because it would preclude such
    # arguments from being specified in a configuration file.
    parser.add_argument(
        '--debug', action='store_true',
        help='Turn on debug logging to stdout')
    parser.add_argument(
        '--config-file', '-c', type=str,
        help='Full path to a JSON configuration file '
             '(command-line arguments override)')
    parser.add_argument(
        '--no-config-file', action='store_true',
        help='Disregard default configuration file, if it exists')
    parser.add_argument(
        '--listen-interface', '-i', type=str, default='0.0.0.0',
        help='Interface to listen on')
    parser.add_argument(
        '--listen-port', '-p', type=int, default=8000,
        help='Port to listen on')
    parser.add_argument(
        '--tls-pemfile', type=str,
        help='Full path to the TLS PEM for the commissaire server')
    parser.add_argument(
        '--tls-clientverifyfile', type=str,
        help='Full path to the TLS file containing the certificate '
             'authorities that client certificates should be verified against')
    parser.add_argument(
        '--authentication-plugin', action='append',
        dest='authentication_plugins',
        metavar='MODULE_NAME:key=value,..', type=parse_to_struct,
        help=('Authentication Plugin module and configuration.'))
    parser.add_argument(
        '--bus-exchange', type=str, default='commissaire',
        help='Message bus exchange name.')
    parser.add_argument(
        '--bus-uri', type=str, metavar='BUS_URI',
        help=(
            'Message bus connection URI. See:'
            'http://kombu.readthedocs.io/en/latest/userguide/connections.html')
    )

    # We have to parse the command-line arguments twice.  Once to extract
    # the --config-file option, and again with the config file content as
    # a baseline.
    args = parser.parse_args()

    if not args.no_config_file:
        # Change dashes to underscores
        json_object = {k.replace('-', '_'): v for k, v in read_config_file(
            args.config_file).items()}
        args = parser.parse_args(namespace=Namespace(**json_object))
    else:
        configured_plugins = {}
        for auth_plugin in args.authentication_plugins:
            configured_plugins.update(auth_plugin)
        args.authentication_plugins = configured_plugins
    return args


class ThreadedWSGIServer(ThreadingMixIn, WSGIServer):
    """
    Threaded version of the WSIServer
    """
    pass


class CommissaireRequestHandler(WSGIRequestHandler):
    """
    Commissaire version of the WSGIRequestHandler.
    """
    #: The software version of the server
    server_version = 'Commissaire/0.0.2'

    def get_environ(self):
        """
        Override to add SSL_CLIENT_VERIFY to the env.

        :returns: The WSGI environment
        :rtype: dict
        """
        env = super(CommissaireRequestHandler, self).get_environ()
        try:
            env['SSL_CLIENT_VERIFY'] = self.request.getpeercert()
        except:
            env['SSL_CLIENT_VERIFY'] = None
        return env


class CommissaireHttpServer:
    """
    Http Server for Commissaire.
    """

    #: Class level logger
    logger = logging.getLogger('CommissaireHttpServer')

    def __init__(self, bind_host, bind_port, dispatcher,
                 tls_pem_file=None, tls_clientverify_file=None):
        """
        Initializes a new CommissaireHttpServer instance.

        :param bind_host: Host adapter to listen on.
        :type bind_host: str
        :param bind_port: Host port to listen on.
        :type bind_port: int
        :param dispatcher: Dispatcher instance (WSGI) to route and respond.
        :type dispatcher: commissaire_http.dispatcher.Dispatcher
        :param tls_pem_file: Full path to the PEM file for TLS.
        :type tls_pem_file: str
        :param tls_clientverify_file: Full path to CA to verify certs.
        :type tls_clientverify_file: str
        """
        # To use the bus call setup_bus()
        self.bus = None
        self._bind_host = bind_host
        self._bind_port = bind_port
        self._tls_pem_file = tls_pem_file
        self._tls_clientverify_file = tls_clientverify_file
        self.dispatcher = dispatcher
        self._httpd = make_server(
            self._bind_host,
            self._bind_port,
            self.dispatcher.dispatch,
            server_class=ThreadedWSGIServer,
            handler_class=CommissaireRequestHandler)

        # If we are given a PEM file then wrap the socket
        if tls_pem_file:
            import ssl
            client_side_cert_kwargs = {}
            if self._tls_clientverify_file:
                client_side_cert_kwargs = {
                    'cert_reqs': ssl.CERT_REQUIRED,
                    'ca_certs': self._tls_clientverify_file,
                }
                self.logger.info(
                    'Requiring client side certificate CA validation.')

            self._httpd.socket = ssl.wrap_socket(
                self._httpd.socket,
                certfile=self._tls_pem_file,
                ssl_version=ssl.PROTOCOL_TLSv1_2,
                server_side=True,
                **client_side_cert_kwargs)
            self.logger.info('Using TLS with {}'.format(self._tls_pem_file))

        self.logger.debug('Created httpd server: {}:{}'.format(
            self._bind_host, self._bind_port))

    def setup_bus(self, exchange_name, connection_url, qkwargs):
        """
        Sets up variables needed for the bus connection.

        :param exchange_name: Name of the topic exchange.
        :type exchange_name: str
        :param connection_url: Kombu connection url.
        :type connection_url: str
        :param qkwargs: One or more dicts keyword arguments for queue creation
        :type qkwargs: list
        """
        self.logger.debug('Setting up bus connection.')
        bus_init_kwargs = {
            'exchange_name': exchange_name,
            'connection_url': connection_url,
            'qkwargs': qkwargs}
        self.bus = Bus(**bus_init_kwargs)
        self.logger.debug('Bus instance created with: {}'.format(
            bus_init_kwargs))
        self.bus.connect()
        # Inject the bus
        self.dispatcher._bus = self.bus
        self.logger.info('Bus connection ready.')

    def serve_forever(self):
        """
        Serve HTTP.
        """
        try:
            self._httpd.serve_forever()
        except Exception as error:
            self.logger.error('Server shut down {}: {}'.format(
                type(error), error))
