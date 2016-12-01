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
Bus related classes and functions.
"""

import logging

from kombu import Connection, Exchange, Producer, Queue

from commissaire.bus import BusMixin
from commissaire.storage.client import StorageClient


class Bus(BusMixin):
    """
    Connection to a bus.
    """

    def __init__(self, exchange_name, connection_url, qkwargs):
        """
        Initializes a new Bus instance.

        :param exchange_name: Name of the topic exchange.
        :type exchange_name: str
        :param connection_url: Kombu connection url.
        :type connection_url: str
        :param qkwargs: One or more dicts keyword arguments for queue creation
        :type qkwargs: list
        """
        self.logger = logging.getLogger('Bus')
        self.logger.debug('Initializing bus connection')
        self.connection = None
        self._channel = None
        self._exchange = None
        self.exchange_name = exchange_name
        self.connection_url = connection_url
        self.qkwargs = qkwargs
        self.storage = StorageClient(self)

    @property
    def init_kwargs(self):
        """
        Returns the initializing kwargs for this instance.

        :returns: the initializing kwargs for this instance.
        :rtype: dict
        """
        return {
            'exchange_name': self.exchange_name,
            'connection_url': self.connection_url,
            'qkwargs': self.qkwargs,
        }

    def connect(self):
        """
        'Connects' to the bus.

        :returns: The same instance.
        :rtype: commissaire_http.bus.Bus
        """
        if self.connection is not None:
            self.logger.warn('Bus already connected.')
            return self

        self.connection = Connection(self.connection_url)
        self._channel = self.connection.channel()
        self._exchange = Exchange(
            self.exchange_name, type='topic').bind(self._channel)
        self._exchange.declare()

        # Create queues
        self._queues = []
        for kwargs in self.qkwargs:
            queue = Queue(**kwargs)
            queue.exchange = self._exchange
            queue = queue.bind(self._channel)
            self._queues.append(queue)
            self.logger.debug('Created queue {}'.format(queue.as_dict()))

        # Create producer for publishing on topics
        self.producer = Producer(self._channel, self._exchange)
        self.logger.debug('Bus connection finished')
        return self

    def respond(self, queue_name, id, payload, **kwargs):  # pragma: no cover
        """
        Sends a response to a simple queue. Responses are sent back to a
        request and never should be the owner of the queue.

        :param queue_name: The name of the queue to use.
        :type queue_name: str
        :param id: The unique request id
        :type id: str
        :param payload: The content of the message.
        :type payload: dict
        :param kwargs: Keyword arguments to pass to SimpleQueue
        :type kwargs: dict
        """
        self.logger.debug('Sending response for message id "{}"'.format(id))
        send_queue = self.connection.SimpleQueue(queue_name, **kwargs)
        jsonrpc_msg = {
            'jsonrpc': "2.0",
            'id': id,
            'result': payload,
        }
        self.logger.debug('jsonrpc msg: {}'.format(jsonrpc_msg))
        send_queue.put(jsonrpc_msg)
        self.logger.debug('Sent response for message id "{}"'.format(id))
        send_queue.close()
