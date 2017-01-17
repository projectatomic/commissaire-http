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
Test for commissaire_http.handlers.networks module.
"""

from unittest import mock

from . import TestCase, expected_error

from commissaire import bus as _bus
from commissaire.constants import JSONRPC_ERRORS
from commissaire_http.handlers import networks, create_jsonrpc_response
from commissaire.models import Network, Networks, ValidationError

# Globals reused in network tests
#: Message ID
ID = '123'
#: Generic network instance
NETWORK = Network.new(name='test')
#: Generic jsonrpc network request by name
SIMPLE_NETWORK_REQUEST = {
    'jsonrpc': '2.0',
    'id': ID,
    'params': {'name': 'test'},
}
#: Generic jsonrpc request with no parameters
NO_PARAMS_REQUEST = {
    'jsonrpc': '2.0',
    'id': ID,
    'params': {}
}


class Test_networks(TestCase):
    """
    Test for the networks handlers.
    """

    def test_list_networks(self):
        """
        Verify list_networks responds with the right information.
        """
        bus = mock.MagicMock()
        bus.storage.list.return_value = Networks.new(networks=[NETWORK])
        self.assertEquals(
            create_jsonrpc_response(ID, ['test']),
            networks.list_networks(NO_PARAMS_REQUEST, bus))

    def test_get_network(self):
        """
        Verify get_network responds with the right information.
        """
        bus = mock.MagicMock()
        bus.storage.get_network.return_value = NETWORK
        self.assertEquals(
            create_jsonrpc_response(ID, NETWORK.to_dict()),
            networks.get_network(SIMPLE_NETWORK_REQUEST, bus))

    def test_create_network(self):
        """
        Verify create_network can create a new network.
        """
        bus = mock.MagicMock()
        # Network doesn't yet exist
        bus.storage.get.side_effect = _bus.StorageLookupError('test', NETWORK)
        # Creation response
        bus.storage.save.return_value = NETWORK
        self.assertEquals(
            create_jsonrpc_response(ID, NETWORK.to_dict()),
            networks.create_network(SIMPLE_NETWORK_REQUEST, bus))

    def test_create_network_idempotent(self):
        """
        Verify create_network acts idempotent.
        """
        bus = mock.MagicMock()
        # Network exists
        bus.storage.get.return_value = NETWORK
        # Creation response
        bus.storage.save.return_value = NETWORK
        self.assertEquals(
            create_jsonrpc_response(ID, NETWORK.to_dict()),
            networks.create_network(SIMPLE_NETWORK_REQUEST, bus))

    def test_create_network_conflict(self):
        """
        Verify create_network rejects conflicting network creation.
        """
        bus = mock.MagicMock()
        bus.storage.get_network.return_value = Network.new(
            name=NETWORK.name, options={'test': 'test'})
        self.assertEquals(
            expected_error(ID, JSONRPC_ERRORS['CONFLICT']),
            networks.create_network(SIMPLE_NETWORK_REQUEST, bus))

    def test_delete_network(self):
        """
        Verify delete_network deletes existing networks.
        """
        bus = mock.MagicMock()
        bus.storage.delete.return_value = None
        self.assertEquals(
            {
                'jsonrpc': '2.0',
                'result': [],
                'id': '123',
            },
            networks.delete_network(SIMPLE_NETWORK_REQUEST, bus))

    def test_delete_network_not_found_on_missing_key(self):
        """
        Verify delete_network returns 404 on a missing network.
        """
        bus = mock.MagicMock()
        bus.storage.delete.side_effect = _bus.RemoteProcedureCallError('test')

        self.assertEquals(
            expected_error(ID, JSONRPC_ERRORS['NOT_FOUND']),
            networks.delete_network(SIMPLE_NETWORK_REQUEST, bus))

    def test_delete_network_internal_error_on_exception(self):
        """
        Verify delete_network returns ISE on any other exception
        """
        # Iterate over a few errors
        for error in (Exception, KeyError, TypeError):
            bus = mock.MagicMock()
            bus.storage.delete.side_effect = error('test')

            self.assertEquals(
                expected_error(ID, JSONRPC_ERRORS['INTERNAL_ERROR']),
                networks.delete_network(SIMPLE_NETWORK_REQUEST, bus))
