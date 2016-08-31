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
import uuid

from queue import Empty
from kombu import Connection, Producer

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

    def __init__(self, router, exchange):
        """
        Initializes a new Dispatcher instance.

        .. todo::

           Make the bus connection configurable.

        :param router: The router to dispatch with.
        :type router: router.TopicRouter
        :param connection: A kombu Exchange.
        :type connection: kombu.Exchange
        """
        self._router = router
        self._bus = Connection('redis://localhost:6379/')
        self._exchange = exchange
        self.producer = Producer(self._bus.channel(), exchange)

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
            environ['PATH_INFO'], environ['REQUEST_METHOD'])
        # If we have a valid route
        if route:
            response_queue_name = 'response-{0}'.format(uuid.uuid4())
            response_queue = self._bus.SimpleQueue(
                response_queue_name,
                queue_opts={'auto_delete': True, 'durable': False})
            # Generate a message and sent it off
            self.producer.publish(
                'An HTTP Request',
                route['topic'],
                reply_to=response_queue_name)
            self.logger.debug(
                'Message sent to {0}. Want {1}.'.format(
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
            # And handle the message based on it's outcome
            if msg.properties.get('outcome') == 'success':
                self.logger.debug(
                    'Got a success. Returning the payload to HTTP.')
                start_response(
                    '200 OK', [('content-type', 'application/json')])
                return [bytes(msg.payload, 'utf8')]
            elif msg.properties.get('outcome') == 'no_data':
                self.logger.debug(
                    'Got a no_data. Returning the payload to HTTP.')
                start_response(
                    '404 Not Found', [('content-type', 'application/json')])
                return [bytes(msg.payload, 'utf8')]
            # TODO: More outcome checks turning responses to HTTP ...
            # If we have an unknown or missing outcome default to ISE
            else:
                self.logger.error(
                    'Unknown outcome: {0}. properties={1}'.format(
                        msg.properties, msg.payload))
                start_response(
                    '500 Internal Server Error',
                    [('content-type', 'text/html')])
                return [bytes('Internal Server Error', 'utf8')]

        # Otherwise handle it as a generic 404
        start_response('404 Not Found', [('content-type', 'text/html')])
        return [bytes('Not Found', 'utf8')]


if __name__ == '__main__':
    from kombu import Exchange
    # See https://gist.github.com/ashcrow/ecb611337dba966c4255697e6c0a204d
    from topicrouter import TopicRouter

    # Make a topic router that takes in "handler"s.
    mapper = TopicRouter()
    mapper.register(
        '^/api/v0/(?P<handler>[a-z]*)/?$',
        'http.{handler}')

    # Create the dispatcher
    exchange = Exchange('commissaire', type='direct')
    d = Dispatcher(mapper, exchange)

    # Fake WSGI start_response
    def start_response(code, properties):
        logger.debug('start_response("{0}",{1})'.format(code, properties))

    print('\n====> I WILL 404')
    print('HTTP BODY: {0}'.format(
        d.dispatch({
            'PATH_INFO': '/idonotexist',
            'REQUEST_METHOD': 'GET'},
            start_response)))
    print('\n====> I WILL WORK')
    print('HTTP BODY: {0}'.format(
        d.dispatch({
            'PATH_INFO': '/api/v0/clusters/',
            'REQUEST_METHOD': 'GET'},
            start_response)))
