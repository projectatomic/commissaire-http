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

from queue import Empty
from kombu import Connection, Exchange, Producer

# NOTE: Only added for this example
logger = logging.getLogger('Dispatcher')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(name)s(%(levelname)s): %(message)s'))
logger.handlers.append(handler)
# --


class Dispatcher:
    """
    Dispatches and translates between HTTP requests and bus services.
    """

    #: Logging instance for all Dispatchers
    logger = logging.getLogger('Router')

    def __init__(self, router, exchange_name, connection_url):
        """
        Initializes a new Dispatcher instance.

        .. todo::

           Make the bus connection configurable.

        :param router: The router to dispatch with.
        :type router: router.TopicRouter
        :param exchange_name: Name of the topic exchange.
        :type exchange_name: str
        :param connection_url: Kombu connection url.
        :type connection_url: str
        """
        self._router = router
        self._connection = Connection(connection_url)
        self._channel = self._connection.channel()
        self._exchange = Exchange(
            exchange_name, 'topic').bind(self._channel)
        self._exchange.declare()
        self.producer = Producer(self._channel, self._exchange)

    def dispatch(self, environ, start_response):
        """
        Dispatches an HTTP request into a bus message, translates the results
        and returns the HTTP response back to the requestor.

        :param environ: WSGI environment dictionary.
        :type environ: dict
        :param start_response: WSGI start_response callable.
        :type start_response: callable
        :returns: The body of the HTTP response.
        :rtype: Mixed

        .. note::

           This prototype is using WSGI but other interfaces could be used.
        """
        route = self._router.match(
            environ['PATH_INFO'], environ)
        # If we have a valid route
        if route:
            id = str(uuid.uuid4())
            response_queue_name = 'response-{0}'.format(id)
            response_queue = self._connection.SimpleQueue(
                response_queue_name,
                queue_opts={'auto_delete': True, 'durable': False})
            jsonrpc_msg = {
                'jsonrpc': '2.0',
                'id': id,
                'method': 'list',
                'params': {},
            }

            # Generate a message and sent it off
            self.producer.publish(
                jsonrpc_msg,
                route['topic'],
                declare=[self._exchange],
                reply_to=response_queue_name)
            self.logger.debug(
                'Message sent to "{0}". Want response on "{1}".'.format(
                    route['topic'], response_queue_name))
            # Get the resulting message back
            try:
                msg = response_queue.get(block=True, timeout=1)
            except Empty:
                # No response before the timeout
                start_response(
                    '502 Bad Gateway', [('content-type', 'text/html')])
                return [bytes('Bad Gateway', 'utf8')]

            msg.ack()
            response_queue.clear()
            response_queue.close()
            self.logger.debug(
                'Received: properties="{0}", payload="{1}"'.format(
                    msg.properties, msg.payload))
            # And handle the message based on it's keys
            if 'result' in msg.payload.keys():
                self.logger.debug(
                    'Got a success. Returning the payload to HTTP.')
                start_response(
                    '200 OK', [('content-type', 'application/json')])
                return [bytes(json.dumps(msg.payload['result']), 'utf8')]
            # elif msg.properties.get('outcome') == 'no_data':
            #     self.logger.debug(
            #         'Got a no_data. Returning the payload to HTTP.')
            #     start_response(
            #         '404 Not Found', [('content-type', 'application/json')])
            #     return [bytes(json.dumps(msg.payload), 'utf8')]
            # TODO: More outcome checks turning responses to HTTP ...
            # If we have an unknown or missing outcome default to ISE
            else:
                self.logger.error(
                    'Unexpected result for message id "{}". "{}"}'.format(
                        id, msg.payload))
                start_response(
                    '500 Internal Server Error',
                    [('content-type', 'text/html')])
                return [bytes('Internal Server Error', 'utf8')]

        # Otherwise handle it as a generic 404
        start_response('404 Not Found', [('content-type', 'text/html')])
        return [bytes('Not Found', 'utf8')]
