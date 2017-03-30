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
Prototype dispatcher.
"""

import logging
import traceback

from importlib import import_module
from inspect import isclass

from commissaire_http.bus import Bus
from commissaire_http.handlers import BasicHandler


def ls_mod(mod, pkg):
    """
    Yields all non internal/protected attributes in a module.

    :param mod: The module itself.
    :type mod:
    :param pkg: The full package name.
    :type pkg: str
    :returns: Tuple of attribute name, attribute, attribute path.
    :rtype: tuple
    """
    for item in dir(mod):
        # Skip all protected and internals
        if not item.startswith('_'):
            attr = getattr(mod, item)
            mod_path = '.'.join([pkg, item])
            yield item, attr, mod_path


class DispatcherError(Exception):  # pragma: no cover
    """
    Dispatcher related errors.
    """
    pass


class Dispatcher:
    """
    Dispatches and translates between HTTP requests and bus services.
    """

    #: Logging instance for all Dispatchers
    logger = logging.getLogger('Dispatcher')

    def __init__(self, router, handler_packages):
        """
        Initializes a new Dispatcher instance.

        :param router: The router to dispatch with.
        :type router: router.TopicRouter
        :param handler_packages: List of packages to load handlers from.
        :type handler_packages: list
        """
        self._router = router
        self._handler_packages = handler_packages
        self._handler_map = {}
        self.reload_handlers()
        self._bus = None

    def setup_bus(self, exchange_name, connection_url, qkwargs):
        """
        Sets up a bus connection with the given configuration.

        Call this method only once after instantiating a Dispatcher.

        :param exchange_name: Name of the topic exchange
        :type exchange_name: str
        :param connection_url: Kombu connection URL
        :type connection_url: str
        :param qkwargs: One or more keyword argument dicts for queue creation
        :type qkwargs: list
        """
        self.logger.debug('Setting up bus connection.')
        bus_init_kwargs = {
            'exchange_name': exchange_name,
            'connection_url': connection_url,
            'qkwargs': qkwargs
        }
        self._bus = Bus(**bus_init_kwargs)
        self.logger.debug(
            'Bus instance created with: %s', bus_init_kwargs)
        self._bus.connect()
        self.logger.info('Bus connection ready.')

    def reload_handlers(self):
        """
        Reloads the handler mapping.
        """
        for pkg in self._handler_packages:
            try:
                mod = import_module(pkg)
                for item, attr, mod_path in ls_mod(mod, pkg):
                    if isinstance(attr, BasicHandler):
                        self._handler_map[mod_path] = attr
                        self.logger.info(
                            'Loaded function handler %s to %s', mod_path, attr)
                    elif (isclass(attr) and issubclass(attr, object) and
                            not issubclass(attr, BasicHandler)):
                        handler_instance = attr()
                        for handler_meth, sub_attr, sub_mod_path in \
                                ls_mod(handler_instance, pkg):
                            key = '.'.join([mod_path, handler_meth])
                            self._handler_map[key] = getattr(
                                handler_instance, handler_meth)
                            self.logger.info(
                                'Instantiated and loaded class '
                                'handler %s to %s', key, handler_instance)
                    else:
                        self.logger.debug(
                            '%s can not be used as a handler.', mod_path)
            except ImportError as error:
                self.logger.error(
                    'Unable to import handler package "{}". {}: {}'.format(
                        pkg, type(error), error))

    def dispatch(self, environ, start_response):
        """
        Dispatches an HTTP request into a jsonrpc message, passes it to a
        handler, translates the results, and returns the HTTP response back
        to the requestor.

        :param environ: WSGI environment dictionary.
        :type environ: dict
        :param start_response: WSGI start_response callable.
        :type start_response: callable
        :returns: The body of the HTTP response.
        :rtype: Mixed
        """
        # Fail early if _bus has never been set.
        if self._bus is None:
            raise DispatcherError(
                'Bus can not be None when dispatching. '
                'Please call dispatcher.setup_bus().')

        # Add the bus instance to the WSGI environment dictionary.
        environ['commissaire.bus'] = self._bus

        # Add the routematch results to the WSGI environment dictionary.
        match_result = self._router.routematch(environ['PATH_INFO'], environ)
        if match_result is None:
            start_response(
                '404 Not Found',
                [('content-type', 'text/html')])
            return [bytes('Not Found', 'utf8')]
        environ['commissaire.routematch'] = match_result

        route_dict = match_result[0]
        route_controller = route_dict['controller']

        try:
            # If the handler registered is a callable, use it
            if callable(route_controller):
                handler = route_controller
            # Else load what we found earlier
            else:
                handler = self._handler_map.get(route_controller)
            self.logger.debug(
                'Using controller %s->%s', route_dict, handler)

            return handler(environ, start_response)
        except Exception as error:
            self.logger.error(
                'Exception raised in handler %s:\n%s',
                route_controller, traceback.format_exc())
            start_response(
                '500 Internal Server Error',
                [('content-type', 'text/html')])
            return [bytes('Internal Server Error', 'utf8')]
