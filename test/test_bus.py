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
Test for commissaire_http.bus
"""

from unittest import mock

from . import TestCase
from commissaire_http.bus import Bus

EXCHANGE = 'exchange'
CONNECTION_URL = 'redis://127.0.0.1:6379//'
QUEUE_KWARGS = [{'name': 'simple', 'routing_key': 'simple.*'}]


class TestBus(TestCase):
    """
    Test for the Bus class.
    """

    def setUp(self):
        """
        Creates a new instance to test with per test.
        """
        self.bus_instance = Bus(EXCHANGE, CONNECTION_URL, QUEUE_KWARGS)

    def test_init_kwargs(self):
        """
        Verify the Bus.init_kwargs returns the arguments used to create the instance.
        """
        self.assertEquals(
            {
                'exchange_name': EXCHANGE,
                'connection_url': CONNECTION_URL,
                'qkwargs': QUEUE_KWARGS,
            },
            self.bus_instance.init_kwargs)

    @mock.patch('commissaire_http.bus.Connection')
    @mock.patch('commissaire_http.bus.Exchange')
    @mock.patch('commissaire_http.bus.Producer')
    def test_connect(self, _producer, _exchange, _connection):
        """
        Verify Bus.connect opens the connection to the bus.
        """
        self.bus_instance.connect()
        # Connection should be called with the proper url
        _connection.assert_called_once_with(self.bus_instance.connection_url)
        _connection().channel.assert_called_once_with()
        # Exchange should be called ...
        _exchange.assert_called_once_with(
            self.bus_instance.exchange_name, type='topic')
        # .. and bound
        # One queue should be Created
        self.assertEqual(1, len(self.bus_instance._queues))
        _exchange().bind.assert_called_once_with(self.bus_instance._channel)
        # We should have a new producer
        _producer.assert_called_once_with(
            self.bus_instance._channel, self.bus_instance._exchange)
