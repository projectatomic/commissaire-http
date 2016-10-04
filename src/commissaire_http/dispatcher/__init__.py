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

import json
import logging
import uuid

from html import escape
from importlib import import_module
from inspect import signature, isfunction, isclass
from urllib.parse import parse_qs

from commissaire_http.bus import Bus
from commissaire_http.constants import JSONRPC_ERRORS


def parse_query_string(qs):
    """
    Parses a query string into parameters.

    :param qs: A query string.
    :type qs: str
    :returns: A dictionary of parameters.
    :rtype: dict
    """
    new_qs = {}
    for key, value in parse_qs(qs).items():
        if len(value) == 1:
            new_qs[key] = escape(value[0])
        else:
            new_value = []
            for item in value:
                new_value.append(escape(item))
            new_qs[key] = new_value
    return new_qs


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

    def reload_handlers(self):
        """
        Reloads the handler mapping.
        """
        for pkg in self._handler_packages:
            try:
                mod = import_module(pkg)
                for item, attr, mod_path in ls_mod(mod, pkg):
                    if isfunction(attr):
                        # Check that it has 2 inputs
                        if len(signature(attr).parameters) == 2:
                            self._handler_map[mod_path] = attr
                            self.logger.info(
                                'Loaded function handler {} to {}'.format(
                                    mod_path, attr))
                    elif isclass(attr) and issubclass(attr, object):
                        handler_instance = attr()
                        for handler_meth, sub_attr, sub_mod_path in \
                                ls_mod(handler_instance, pkg):
                            key = '.'.join([mod_path, handler_meth])
                            self._handler_map[key] = getattr(
                                handler_instance, handler_meth)
                            self.logger.info(
                                'Instansiated and loaded class handler '
                                '{} to {}'.format(key, handler_instance))
                    else:
                        self.logger.debug(
                            '{} can not be used as a handler.'.format(
                                mod_path))
            except ImportError as error:
                self.logger.error(
                    'Unable to import handler package "{}". {}: {}'.format(
                        pkg, type(error), error))

    def _get_params(self, environ, route, route_data):
        """
        Handles pulling parameters out of the various inputs.

        :param environ: WSGI environment dictionary.
        :type environ: dict
        :param route: The route structure returned by a routematch.
        :type route: dict
        :param route_data: Specific internals on a matched route.
        :type route_data: dict
        :returns: The found parameters.
        :rtype: dict
        """
        params = {}
        # Initial params come from the urllib
        for param_key in route_data.minkeys:
            params[param_key] = route[param_key]

        # If we are a PUT or POST look for params in wsgi.input
        if environ['REQUEST_METHOD'] in ('PUT', 'POST'):
            if environ.get('CONTENT_LENGTH') and environ['CONTENT_LENGTH']:
                try:
                    params.update(json.loads(environ['wsgi.input'].read(
                        int(environ['CONTENT_LENGTH'])).decode()))
                except json.decoder.JSONDecodeError as error:
                    self.logger.debug(
                        'Unable to read "wsgi.input": {}'.format(error))
        else:
            params.update(parse_query_string(environ.get('QUERY_STRING')))
        return params

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
        route_info = self._router.routematch(environ['PATH_INFO'], environ)

        # If we have valid route_info
        if route_info:
            # Split up the route from the route data
            route, route_data = route_info

            # Get the parameter
            params = self._get_params(environ, route, route_data)

            # method is normally supposed to be the method to be called
            # but we hijack it for the method that was used over HTTP
            jsonrpc_msg = {
                'jsonrpc': '2.0',
                'id': str(uuid.uuid4()),
                'method': environ['REQUEST_METHOD'],
                'params': params,
            }

            self.logger.debug(
                'Request transformed to "{}".'.format(jsonrpc_msg))
            # Get the resulting message back
            try:
                handler = self._handler_map.get(route['controller'])
                self.logger.debug('Using controller {}->{}'.format(
                    route, handler))
                # Pass the message and, if needed, a new instance of the
                # bus to the handler
                bus = None
                if self._bus:
                    bus = Bus(**self._bus.init_kwargs).connect()

                result = handler(jsonrpc_msg, bus=bus)
                self.logger.debug(
                    'Handler {} returned "{}"'.format(
                        route['controller'], result))
                if 'error' in result.keys():
                    error = result['error']
                    # If it's Invalid params handle it
                    if error['code'] == JSONRPC_ERRORS['BAD_REQUEST']:
                        start_response(
                            '400 Bad Request',
                            [('content-type', 'application/json')])
                        return [bytes(json.dumps(error), 'utf8')]
                    if error['code'] == JSONRPC_ERRORS['NOT_FOUND']:
                        start_response(
                            '404 Not Found',
                            [('content-type', 'application/json')])
                        return [bytes(json.dumps(error), 'utf8')]

                    # Otherwise treat it like a 500 by raising
                    raise Exception(result['error'])
                elif 'result' in result.keys():
                    start_response(
                        '200 OK', [('content-type', 'application/json')])
                    return [bytes(json.dumps(result['result']), 'utf8')]
            except Exception as error:
                self.logger.error(
                    'Exception raised while {} handled "{}". {}: {}'.format(
                        route['controller'], jsonrpc_msg, type(error), error))
                start_response(
                    '500 Internal Server Error',
                    [('content-type', 'text/html')])
                return [bytes('Internal Server Error', 'utf8')]

        # Otherwise handle it as a generic 404
        start_response('404 Not Found', [('content-type', 'text/html')])
        return [bytes('Not Found', 'utf8')]
