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
Commissaire HTTP based application server.
"""
import argparse
import importlib
import logging

from commissaire_http.server.routing import DISPATCHER
from commissaire_http import CommissaireHttpServer, parse_args


# TODO: Make this configurable
for name in ('Dispatcher', 'Router', 'Bus', 'CommissaireHttpServer'):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '%(name)s(%(levelname)s): %(message)s'))
    logger.handlers.append(handler)
# --


def inject_authentication(plugin, kwargs):
    """
    Injects authentication into the dispatcher's dispatch method.

    :param plugin: Name of the Authenticator plugin.
    :type plugin: str
    :param kwargs: Arguments for the Authenticator
    :type kwargs: dict or list
    :returns: A wrapped Dispatcher instance
    :rtype: commissaire.dispatcher.Dispatcher
    """
    module = importlib.import_module(plugin)
    authentication_class = getattr(module, 'AuthenticationPlugin')

    authentication_kwargs = {}
    if type(kwargs) is str:
        if '=' in kwargs:
            for item in kwargs.split(','):
                key, value = item.split('=')
                authentication_kwargs[key.strip()] = value.strip()
    elif type(kwargs) is dict:
        # _read_config_file() sets this up.
        authentication_kwargs = kwargs

    # NOTE: We wrap only the dispatch method, not the entire
    #       dispatcher instance.
    DISPATCHER.dispatch = authentication_class(
        DISPATCHER.dispatch, **authentication_kwargs)
    return DISPATCHER


def main():
    """
    Main entry point.
    """
    epilog = 'Example: commissaire -c conf/myconfig.json'
    parser = argparse.ArgumentParser(epilog=epilog)
    args = parse_args(parser)

    try:
        # Inject the authentication plugin
        if args.authentication_plugin:
            DISPATCHER = inject_authentication(
                args.authentication_plugin, args.authentication_plugin_kwargs)

        # Create the server
        server = CommissaireHttpServer(
            args.listen_interface,
            args.listen_port,
            DISPATCHER,
            args.tls_pemfile,
            args.tls_clientverifyfile)

        # Set up our bus data
        server.setup_bus(
            args.bus_exchange,
            args.bus_uri,
            [{'name': 'simple', 'routing_key': 'simple.*'}])

        # Serve until we are killed off
        server.serve_forever()
    except KeyboardInterrupt:  # pragma: no cover
        pass
    except ImportError:
        parser.error('Could not import "{}" for authentication'.format(
            args.authentication_plugin))
    except Exception as error:  # pragma: no cover
        from traceback import print_exc
        print_exc()
        parser.error('Exception shown above. Error: {}'.format(error))


if __name__ == '__main__':  # pragma: no cover
    main()
