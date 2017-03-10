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
Test for commissaire_http.handlers.clusters module.
"""

import copy

from unittest import mock

from . import TestCase, expected_error

from commissaire import constants as C
from commissaire import bus as _bus
from commissaire.constants import JSONRPC_ERRORS
from commissaire_http.handlers import create_jsonrpc_response, clusters
from commissaire.models import Cluster, Clusters, Hosts, Network, ValidationError


# Globals reused in cluster tests
#: Message ID
ID = '123'
#: Generic cluster model
CLUSTER = Cluster.new(name='test')
#: Generic cluster model with container manager
CLUSTER_WITH_CONTAINER_MANAGER = Cluster.new(
    name='test', container_manager=C.CONTAINER_MANAGER_OPENSHIFT)
#: Generic jsonrpc cluster request with name
SIMPLE_CLUSTER_REQUEST = {
    'jsonrpc': '2.0',
    'id': ID,
    'params': CLUSTER.to_dict(),
}
#: Generic jsonrpc cluster request with name and network
NETWORK_CLUSTER_REQUEST = {
    'jsonrpc': '2.0',
    'id': ID,
    'params': {
        'name': CLUSTER.name,
        'network': 'test',
    },
}
#: Generic jsonrpc cluster member request with name and host
CHECK_CLUSTER_REQUEST = {
    'jsonrpc': '2.0',
    'id': ID,
    'params': {
        'name': CLUSTER.name,
        'host': '127.0.0.1',
    },
}
#: Generic jsonrpc request with no parameters
NO_PARAMS_REQUEST = {
    'jsonrpc': '2.0',
    'id': ID,
    'params': {}
}

class Test_clusters(TestCase):
    """
    Test for the clusters handlers.
    """

    def test_list_clusters(self):
        """
        Verify list_clusters responds with the right information.
        """
        bus = mock.MagicMock()
        bus.storage.list.return_value = Clusters.new(clusters=[CLUSTER])
        self.assertEquals(
            create_jsonrpc_response(ID, [CLUSTER.name]),
            clusters.list_clusters.handler(NO_PARAMS_REQUEST, bus))

    def test_get_cluster(self):
        """
        Verify get_cluster responds with the right information.
        """
        bus = mock.MagicMock()
        # Cluster request
        bus.storage.get_cluster.return_value = CLUSTER
        self.assertEquals(
            create_jsonrpc_response(ID, {
                'name': 'test',
                'hostset': [],
                'hosts': {'available': 0, 'total': 0, 'unavailable': 0},
                'network': 'default',
                'status': C.CLUSTER_STATUS_OK,
                'container_manager': '',
            }),
            clusters.get_cluster.handler(SIMPLE_CLUSTER_REQUEST, bus))

    def test_create_cluster(self):
        """
        Verify create_cluster saves new clusters.
        """
        bus = mock.MagicMock()
        bus.storage.get_cluster.side_effect = Exception
        bus.storage.save.return_value = CLUSTER

        self.assertEquals(
            create_jsonrpc_response(ID, CLUSTER.to_dict_safe()),
            clusters.create_cluster.handler(SIMPLE_CLUSTER_REQUEST, bus))

    def test_create_cluster_with_invalid_data(self):
        """
        Verify create_cluster saves new clusters.
        """
        bus = mock.MagicMock()
        # names must be a str, not an int
        bad_cluster = Cluster.new(name=123)

        bus.storage.get_cluster.side_effect = Exception
        bus.storage.save.side_effect = ValidationError

        self.assertEquals(
            expected_error(ID, JSONRPC_ERRORS['INVALID_REQUEST']),
            clusters.create_cluster.handler({
                'jsonrpc': '2.0',
                'id': ID,
                'params': {'name': bad_cluster.name}
                }, bus))

    def test_create_cluster_with_valid_network(self):
        """
        Verify create_cluster uses valid networks as expected.
        """
        bus = mock.MagicMock()
        cluster = Cluster.new(name='test', network='test')
        # The cluster doesn't exist yet
        bus.storage.get_cluster.side_effect = Exception
        # Network response
        bus.storage.get_network.return_value = Network.new(name='test')
        # Creation of the cluster
        bus.storage.save.return_value = cluster

        # Call the handler...
        clusters.create_cluster.handler(copy.deepcopy(NETWORK_CLUSTER_REQUEST), bus)

        bus.storage.save.assert_called_with(mock.ANY)

    def test_create_cluster_with_invalid_network(self):
        """
        Verify create_cluster reacts to invalid networks as expected.
        """
        bus = mock.MagicMock()
        cluster = Cluster.new(name='test', network='test')
        # The cluster doesn't exist yet
        bus.storage.get_cluster.side_effect = Exception
        # The network doesn't exist
        bus.storage.get_network.side_effect = Exception
        # The cluster creation
        bus.storage.save.return_value = cluster

        # Call the handler...
        clusters.create_cluster.handler(copy.deepcopy(NETWORK_CLUSTER_REQUEST), bus)
        # Update clusters network to be 'default' as we expect 'test' to be
        # rejected by the handler
        cluster.network = 'default'
        bus.storage.save.assert_called_with(mock.ANY)

    def test_delete_cluster(self):
        """
        Verify delete_cluster deletes existing clusters.
        """
        bus = mock.MagicMock()
        # Cluster request
        bus.storage.get_cluster.return_value = CLUSTER
        # The delete shouldn't return anything
        bus.storage.delete.return_value = None
        self.assertEquals(
            create_jsonrpc_response(ID, []),
            clusters.delete_cluster.handler(SIMPLE_CLUSTER_REQUEST, bus))
        # Verify we did NOT have a 'container.remove_all_nodes'
        # XXX Fragile; will break if another bus.request call is added.
        bus.request.assert_not_called()

    def test_delete_cluster_with_container_manager(self):
        """
        Verify delete_cluster with a container manager.
        """
        bus = mock.MagicMock()
        # Cluster request
        bus.storage.get_cluster.return_value = CLUSTER_WITH_CONTAINER_MANAGER
        # The delete shouldn't return anything
        bus.storage.delete.return_value = None
        self.assertEquals(
            create_jsonrpc_response(ID, []),
            clusters.delete_cluster.handler(SIMPLE_CLUSTER_REQUEST, bus))
        # Verify we had a 'container.remove_all_nodes'
        bus.request.assert_called_with('container.remove_all_nodes', params=mock.ANY)

    def test_delete_cluster_that_does_not_exist(self):
        """
        Verify delete_cluster returns properly when the cluster doesn't exist.
        """
        bus = mock.MagicMock()
        bus.storage.get_cluster.side_effect = _bus.StorageLookupError('test')
        self.assertEquals(
            expected_error(ID, JSONRPC_ERRORS['NOT_FOUND']),
            clusters.delete_cluster.handler(SIMPLE_CLUSTER_REQUEST, bus))

    def test_delete_cluster_on_unexpected_error(self):
        """
        Verify delete_cluster returns properly when an unexpected error occurs.
        """
        bus = mock.MagicMock()
        bus.storage.delete.side_effect = Exception('test')
        self.assertEquals(
            expected_error(ID, JSONRPC_ERRORS['INTERNAL_ERROR']),
            clusters.delete_cluster.handler(SIMPLE_CLUSTER_REQUEST, bus))

    def test_list_cluster_members(self):
        """
        Verify that list_cluster_members returns proper information.
        """
        bus = mock.MagicMock()
        bus.storage.get_cluster.return_value = Cluster.new(
            name='test', hostset=['127.0.0.1'])
        self.assertEquals(
            create_jsonrpc_response(ID, ['127.0.0.1']),
            clusters.list_cluster_members.handler(SIMPLE_CLUSTER_REQUEST, bus))

    def test_update_cluster_members_with_valid_input(self):
        """
        Verify that update_cluster_members handles valid input.
        """
        bus = mock.MagicMock()
        cluster = Cluster.new(
            name='test', hostset=['127.0.0.1'])

        bus.storage.get_cluster.return_value = cluster
        bus.storage.save.return_value = cluster

        result = clusters.update_cluster_members.handler({
            'jsonrpc': '2.0',
            'id': '123',
            'params': {'name': 'test', 'old': ['127.0.0.1'], 'new': []}
        }, bus)

        self.assertEquals([], result['result']['hostset'])

    def test_update_cluster_members_with_conflicting_input(self):
        """
        Verify that update_cluster_members handles conflicting input.
        """
        bus = mock.MagicMock()
        cluster = Cluster.new(
            name='test', hostset=['127.0.0.1'])

        bus.storage.get_cluster.return_value = cluster

        result = clusters.update_cluster_members.handler({
            'jsonrpc': '2.0',
            'id': '123',
            'params': {'name': 'test', 'old': [], 'new': []}
        }, bus)

        self.assertEquals(
            expected_error(ID, JSONRPC_ERRORS['CONFLICT']),
            result)

    def test_update_cluster_members_with_missing_params(self):
        """
        Verify that update_cluster_members handles missing old/new params.
        """
        for params in (
                {},
                {'old': []},
                {'new': []}):
            result = clusters.update_cluster_members.handler({
                'jsonrpc': '2.0',
                'id': ID,
                'params': params,
                }, mock.MagicMock())
            self.assertEquals(
                expected_error(ID, JSONRPC_ERRORS['BAD_REQUEST']),
                result
            )

    def test_check_cluster_member_with_valid_member(self):
        """
        Verify that check_cluster_member returns proper data when a valid member is requested.
        """
        bus = mock.MagicMock()
        cluster = Cluster.new(
            name='test', hostset=['127.0.0.1'])

        bus.storage.get_cluster.return_value = cluster

        self.assertEquals(
            create_jsonrpc_response(ID, ['127.0.0.1']),
            clusters.check_cluster_member.handler(CHECK_CLUSTER_REQUEST, bus))

    def test_check_cluster_member_with_invalid_member(self):
        """
        Verify that check_cluster_member returns proper data when an invalid member is requested.
        """
        bus = mock.MagicMock()
        cluster = Cluster.new(
            name='test', hostset=['127.0.0.1'])

        bus.storage.get_cluster.return_value = cluster

        result = clusters.check_cluster_member.handler({
            'jsonrpc': '2.0',
            'id': ID,
            'params': {'name': 'test', 'host': '127.0.0.2'}
        }, bus)

        self.assertEquals(
            expected_error(ID, JSONRPC_ERRORS['NOT_FOUND']),
            result)

    def test_add_cluster_member_with_valid_member(self):
        """
        Verify that add_cluster_member actually adds a new member..
        """
        bus = mock.MagicMock()
        cluster = Cluster.new(
            name='test', hostset=[])

        bus.storage.get_cluster.return_value = cluster
        bus.storage.save.return_value = None

        expected_response = create_jsonrpc_response(ID, ['127.0.0.1'])
        self.assertEquals(
            expected_response,
            clusters.add_cluster_member.handler(CHECK_CLUSTER_REQUEST, bus))

    def test_delete_cluster_member_with_valid_member(self):
        """
        Verify that delete_cluster_member actually removes a member.
        """
        bus = mock.MagicMock()
        cluster = Cluster.new(
            name='test', hostset=['127.0.0.1'])

        bus.storage.get_cluster.return_value = cluster
        bus.storage.save.return_value = None

        self.assertEquals(
            create_jsonrpc_response(ID, []),
            clusters.delete_cluster_member.handler(CHECK_CLUSTER_REQUEST, bus))

        # Verify we did NOT have a 'container.remove_node'
        # XXX Fragile; will break if another bus.request call is added.
        bus.request.assert_not_called()

    def test_delete_cluster_member_with_container_manager(self):
        """
        Verify that delete_cluster_member handles a container manager
        """
        bus = mock.MagicMock()
        cluster = Cluster.new(
            name='test', hostset=['127.0.0.1'],
            container_manager=C.CONTAINER_MANAGER_OPENSHIFT)

        bus.storage.get_cluster.return_value = cluster
        bus.storage.save.return_value = None

        self.assertEquals(
            create_jsonrpc_response(ID, []),
            clusters.delete_cluster_member.handler(CHECK_CLUSTER_REQUEST, bus))

        # Verify we had a 'container.remove_node'
        bus.request.assert_called_with('container.remove_node', params=mock.ANY)
