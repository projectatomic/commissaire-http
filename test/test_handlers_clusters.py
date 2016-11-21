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

from commissaire import bus as _bus
from commissaire.constants import JSONRPC_ERRORS
from commissaire_http.handlers import create_response, clusters
from commissaire.models import Cluster, Network, ValidationError


# Globals reused in cluster tests
#: Message ID
ID = '123'
#: Generic jsonrpc cluster by name
CLUSTER = Cluster.new(name='test')
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
#: Generic jsonrpc cluster memeber request with name and host
CHECK_CLUSTER_REQUEST = {
    'jsonrpc': '2.0',
    'id': ID,
    'params': {
        'name': CLUSTER.name,
        'host': '127.0.0.1',
    },
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
        bus.request.return_value = create_response(ID, [{'name': 'test'}])
        self.assertEquals(
            create_response(ID, [CLUSTER.name]),
            clusters.list_clusters(bus.request.return_value, bus))

    def test_get_cluster(self):
        """
        Verify get_cluster responds with the right information.
        """
        bus = mock.MagicMock()
        bus.request.side_effect = (
            # Cluster requests
            create_response(ID, {'name': CLUSTER.name}),
            # Hosts requests
            create_response(ID, []))
        self.assertEquals(
            create_response(ID, {
                'name': 'test',
                'hosts': {'available': 0, 'total': 0, 'unavailable': 0},
                'network': 'default',
                'status': '',
                'container_manager': '',
            }),
            clusters.get_cluster(SIMPLE_CLUSTER_REQUEST, bus))

    def test_create_cluster(self):
        """
        Verify create_cluster saves new clusters.
        """
        bus = mock.MagicMock()
        cluster_json = Cluster.new(name='test').to_json()
        bus.request.return_value = create_response(ID, cluster_json)

        self.assertEquals(
            create_response(ID, cluster_json),
            clusters.create_cluster(SIMPLE_CLUSTER_REQUEST, bus))

    def test_create_cluster_with_invalid_data(self):
        """
        Verify create_cluster saves new clusters.
        """
        bus = mock.MagicMock()
        # names must be a str, not an int
        bad_cluster = Cluster.new(name=123)

        bus.request.side_effect = Exception

        self.assertEquals(
            expected_error(ID, JSONRPC_ERRORS['INVALID_REQUEST']),
            clusters.create_cluster({
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
        bus.request.side_effect = (
            # The cluster doesn't exist yet
            Exception,
            # Network response
            Network.new(name='test'),
            # Creation of the cluster
            create_response(ID, cluster.to_json()),
        )

        # Call the handler...
        clusters.create_cluster(copy.deepcopy(NETWORK_CLUSTER_REQUEST), bus)

        bus.request.assert_called_with(
            'storage.save', params=[
                'Cluster', cluster.to_dict()])

    def test_create_cluster_with_invalid_network(self):
        """
        Verify create_cluster reacts to invalid networks as expected.
        """
        bus = mock.MagicMock()
        cluster = Cluster.new(name='test', network='test')
        bus.request.side_effect = (
            # The cluster doesn't exist yet
            Exception,
            # The network doesn't exist
            Exception,
            # The cluster creation
            create_response(ID, cluster.to_json()),
        )

        # Call the handler...
        clusters.create_cluster(copy.deepcopy(NETWORK_CLUSTER_REQUEST), bus)
        # Update clusters network to be 'default' as we expect 'test' to be
        # rejected by the handler
        cluster.network = 'default'
        bus.request.assert_called_with(
            'storage.save', params=[
                'Cluster', cluster.to_dict()])

    def test_delete_cluster(self):
        """
        Verify delete_cluster deletes existing clusters.
        """
        bus = mock.MagicMock()
        bus.request.side_effect = (
            # The delete shouldn't return anything
            None,
        )
        self.assertEquals(
            create_response(ID, []),
            clusters.delete_cluster(SIMPLE_CLUSTER_REQUEST, bus))

    def test_delete_cluster_that_does_not_exist(self):
        """
        Verify delete_cluster returns properly when the cluster doesn't exist.
        """
        bus = mock.MagicMock()
        bus.request.side_effect = (
            _bus.RemoteProcedureCallError('test')
        )
        self.assertEquals(
            expected_error(ID, JSONRPC_ERRORS['NOT_FOUND']),
            clusters.delete_cluster(SIMPLE_CLUSTER_REQUEST, bus))

    def test_delete_cluster_on_unexpected_error(self):
        """
        Verify delete_cluster returns properly when an unexpected error occurs.
        """
        bus = mock.MagicMock()
        bus.request.side_effect = (
            Exception('test')
        )
        self.assertEquals(
            expected_error(ID, JSONRPC_ERRORS['INTERNAL_ERROR']),
            clusters.delete_cluster(SIMPLE_CLUSTER_REQUEST, bus))

    def test_list_cluster_members(self):
        """
        Verify that list_cluster_members returns proper information.
        """
        bus = mock.MagicMock()
        bus.request.return_value = {
            'jsonrpc': '2.0',
            'result': Cluster.new(
                name='test', hostset=['127.0.0.1']).to_dict(),
            'id': ID}
        self.assertEquals(
            create_response(ID, ['127.0.0.1']),
            clusters.list_cluster_members(SIMPLE_CLUSTER_REQUEST, bus))

    def test_update_cluster_members_with_valid_input(self):
        """
        Verify that update_cluster_members handles valid input.
        """
        bus = mock.MagicMock()
        cluster = Cluster.new(
            name='test', hostset=['127.0.0.1'])

        bus.request.return_value = create_response(ID, cluster.to_dict())

        result = clusters.update_cluster_members({
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

        bus.request.return_value = create_response(ID, cluster.to_dict())

        result = clusters.update_cluster_members({
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
            result = clusters.update_cluster_members({
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

        bus.request.return_value = create_response(ID, cluster.to_dict())

        self.assertEquals(
            create_response(ID, ['127.0.0.1']),
            clusters.check_cluster_member(CHECK_CLUSTER_REQUEST, bus))

    def test_check_cluster_member_with_invalid_member(self):
        """
        Verify that check_cluster_member returns proper data when an invalid member is requested.
        """
        bus = mock.MagicMock()
        cluster = Cluster.new(
            name='test', hostset=['127.0.0.1'])

        bus.request.return_value = create_response(ID, cluster.to_dict())

        result = clusters.check_cluster_member({
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

        bus.request.return_value = create_response(ID, cluster.to_dict())
        expected_response = create_response(ID, ['127.0.0.1'])
        self.assertEquals(
            expected_response,
            clusters.add_cluster_member(CHECK_CLUSTER_REQUEST, bus))

    def test_delete_cluster_member_with_valid_member(self):
        """
        Verify that delete_cluster_member actually removes a member.
        """
        bus = mock.MagicMock()
        cluster = Cluster.new(
            name='test', hostset=['127.0.0.1'])

        bus.request.return_value = create_response(ID, cluster.to_dict())
        self.assertEquals(
            create_response(ID, []),
            clusters.delete_cluster_member(CHECK_CLUSTER_REQUEST, bus))
