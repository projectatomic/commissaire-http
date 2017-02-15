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

from commissaire.util.config import import_plugin

from commissaire_http.authentication import (
    AuthenticationManager, Authenticator)
from commissaire_http.server.routing import DISPATCHER  # noqa
from commissaire_http import CommissaireHttpServer, parse_args


def inject_authentication(plugins):
    """
    Injects authentication into the dispatcher's dispatch method.

    :param plugin: Name of the Authenticator plugin.
    :type plugin: str
    :param kwargs: Arguments for the Authenticator
    :type kwargs: dict or list
    :returns: A wrapped Dispatcher instance
    :rtype: commissaire.dispatcher.Dispatcher
    """
    global DISPATCHER
    authn_manager = AuthenticationManager(DISPATCHER.dispatch)
    for module_name in plugins:
        authentication_class = import_plugin(
            module_name, 'commissaire_http.authentication', Authenticator)
        # NOTE: We set the app to None as we are not using the
        #       authentication_class as the dispatcher itself
        authn_manager.authenticators.append(
            authentication_class(None, **plugins[module_name]))

    # If there are no authentication managers defined, append the default
    # which will deny all requests
    if len(authn_manager.authenticators) == 0:
        print(
            'No authentication plugins found. Denying all requests.')
        authn_manager.authenticators.append(Authenticator(None))

    # NOTE: We wrap only the dispatch method, not the entire
    #       dispatcher instance.
    DISPATCHER.dispatch = authn_manager
    return DISPATCHER


def main():
    """
    Main entry point.
    """
    # Use the same dispatcher
    global DISPATCHER

    epilog = 'Example: commissaire -c conf/myconfig.json'
    parser = argparse.ArgumentParser(epilog=epilog)
    args = parse_args(parser)

    try:
        # Inject the authentication plugin
        DISPATCHER = inject_authentication(args.authentication_plugins)

        # Connect to the bus
        DISPATCHER.setup_bus(
            args.bus_exchange,
            args.bus_uri,
            [{'name': 'simple', 'routing_key': 'simple.*'}])

        # Create the server
        server = CommissaireHttpServer(
            args.listen_interface,
            args.listen_port,
            DISPATCHER,
            args.tls_pemfile,
            args.tls_clientverifyfile)

        # Serve until we are killed off
        server.serve_forever()
    except KeyboardInterrupt:  # pragma: no cover
        pass
    except ImportError:
        parser.error('Could not import "{}" for authentication'.format(
            args.authentication_plugins))
    except Exception as error:  # pragma: no cover
        from traceback import print_exc
        print_exc()
        parser.error('Exception shown above. Error: {}'.format(error))


if __name__ == '__main__':  # pragma: no cover
    main()
