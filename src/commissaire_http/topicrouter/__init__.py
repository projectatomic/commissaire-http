#!/usr/bin/env python
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
Prototype router.
"""


import re
import logging

# NOTE: Only added for this example
r = logging.getLogger('Router')
r.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(name)s(%(levelname)s): %(message)s'))
r.handlers.append(handler)
# --


class TopicRouter:
    """
    An URL router which maps to AMQP topics.
    """

    #: Logging instance for all Routers
    logger = logging.getLogger('Router')

    def __init__(self):
        """
        Initializes a new TopicRouter instance.
        """
        self._routes = {}

    def __repr__(self):
        """
        Creates and returns a string representation of the instance.
        """
        pretty = ''
        for x in self._routes.values():
            pretty += 'Route="{0}" to "{1}" for Methods "{2}"'.format(
                x['path'], x['topic'], ', '.join(x['methods']))
        return pretty

    def register(self, path, topic, methods=['GET']):
        """
        Registers a URL path to a topic. When named groups are specified
        in the path they can be used in the topic by using {NAME} syntax.

        Example::

           mapper.register(
               '^/my/(?P<handler>\w+)/',
               'handlers.{handler}',
               ['GET', 'PUT', 'DELETE'])

        :param path: Regular expression string of the path.
        :type path: str
        :param topic: The topic template.
        :type topic: str
        :param methods: A list of accepted methods. Default only accepts GET.
        :type methods: list
        """
        methods = [m.upper() for m in methods]
        self._routes[path] = {
            'compiled': re.compile(path),
            'path': path,
            'topic': topic,
            'methods': methods,
        }
        self.logger.info('Registered: {0}'.format(self._routes[path]))

    def match(self, path, method):
        """
        Looks for a match for a path/method combination.

        :param path: The URL path to match.
        :type path: str
        :param method: The HTTP method to match.
        :type method: str
        :returns: A dict containting routing information or None if no route.
        :rtype: dict or None
        """
        path_method = 'path="{0}" method="{1}"'.format(path, method)
        self.logger.debug('Looking for a route for {0}...'.format(path_method))
        for route in self._routes.values():
            match = route['compiled'].match(path)
            if match:
                self.logger.debug(
                    'Found match for {0}. {1}. Checking methods...'.format(
                        path_method, route['path']))
                if method.upper() in route['methods']:

                    topic_kwargs = {}
                    if match.groups:
                        topic_kwargs = match.groupdict()

                    return_route = {
                        'compiled': route['compiled'],
                        'path': path,
                        'topic': route['topic'].format(**topic_kwargs),
                        'methods': route['methods'],
                    }

                    self.logger.debug(
                        'Found solid match for {0}. {1}'.format(
                            path_method, return_route))
                    return return_route

        self.logger.debug('No route fully matched {0}'.format(path_method))
        return None


if __name__ == '__main__':
    MAPPER = TopicRouter()
    MAPPER.register(
        '^/api/v0/(?P<handler>[a-z]*)/?$',
        'http.{handler}')
    print('=> I SHOULD FAIL')
    print(MAPPER.match('/fail', 'get'))
    print('=> I SHOULD WORK')
    print(MAPPER.match('/api/v0/clusters/', 'get'))
