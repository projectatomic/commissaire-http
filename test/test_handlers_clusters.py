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

from unittest import mock

from . import TestCase

from commissaire.constants import JSONRPC_ERRORS
from commissaire_http.handlers import create_response, clusters
from commissaire.models import Cluster, Network, ValidationError


class Test_clusters(TestCase):
    """
    Test for the clusters handlers.
    """

    def test_list_clusters(self):
        """
        Verify list_clusters responds with the right information.
        """
        bus = mock.MagicMock()
        bus.request.return_value = {
            'jsonrpc': '2.0',
            'result': [{'name': 'test'}],
            'id': '123'}
        self.assertEquals(
            {
                'jsonrpc': '2.0',
                'result': ['test'],
                'id': '123',
            },
            clusters.list_clusters(bus.request.return_value, bus))

    def test_get_cluster(self):
        """
        Verify get_cluster responds with the right information.
        """
        bus = mock.MagicMock()
        bus.request.side_effect = (
            # Cluster requests
            {
                'jsonrpc': '2.0',
                'result': {'name': 'test'},
                'id': '123',
            },
            # Hosts requests
            {
                'jsonrpc': '2.0',
                'result': [],
                'id': '123',
            })
        self.assertEquals(
            {
                'jsonrpc': '2.0',
                'result': {
                    'name': 'test',
                    'hosts': {'available': 0, 'total': 0, 'unavailable': 0},
                    'network': 'default',
                    'status': '',
                    'type': 'kubernetes',
                },
                'id': '123',
            },
            clusters.get_cluster({
                'jsonrpc': '2.0',
                'id': '123',
                'params': {'name': 'test'}
                }, bus))

    def test_create_cluster(self):
        """
        Verify create_cluster saves new clusters.
        """
        bus = mock.MagicMock()
        cluster_json = Cluster.new(name='test').to_json()
        bus.request.return_value = {
            'jsonrpc': '2.0',
            'result': cluster_json,
            'id': '123'}

        self.assertEquals(
            {
                'jsonrpc': '2.0',
                'result': cluster_json,
                'id': '123',
            },
            clusters.create_cluster({
                'jsonrpc': '2.0',
                'id': '123',
                'params': {'name': 'test'}
                }, bus))

    def test_create_cluster_with_invalid_data(self):
        """
        Verify create_cluster saves new clusters.
        """
        bus = mock.MagicMock()
        # names must be a str, not an int
        cluster = Cluster.new(name=123)

        bus.request.side_effect = Exception

        # Create the response we expect
        expected_response =  create_response(
            id='123',
            error=ValidationError('test'),
            error_code=-32602)
        # Ignore checking the message. Just verify it exists.
        expected_response['error']['message'] = mock.ANY

        self.assertEquals(
            expected_response,
            clusters.create_cluster({
                'jsonrpc': '2.0',
                'id': '123',
                'params': {'name': 123}
                }, bus))

    def test_create_cluster_with_valid_network(self):
        """
        Verify create_cluster uses valid networks as expected.
        """
        bus = mock.MagicMock()
        cluster = Cluster.new(name='test', network='test')
        bus.request.side_effect = (
            Exception,
            Network.new(name='test'),
            {
                'jsonrpc': '2.0',
                'result': cluster.to_json(),
                'id': '123',
            },
        )

        # Call the handler...
        clusters.create_cluster({
            'jsonrpc': '2.0',
            'id': '123',
            'params': {'name': 'test', 'network': 'test'}
            }, bus)
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
            Exception,
            Exception,
            {
                'jsonrpc': '2.0',
                'result': cluster.to_json(),
                'id': '123',
            },
        )

        # Call the handler...
        clusters.create_cluster({
            'jsonrpc': '2.0',
            'id': '123',
            'params': {'name': 'test', 'network': 'test'}
            }, bus)
        # Update clusters network to be 'default' as we expect 'test' to be
        # rejected by the handler
        cluster.network = 'default'
        bus.request.assert_called_with(
            'storage.save', params=[
                'Cluster', cluster.to_dict()])

    def test_list_cluster_members(self):
        """
        Verify that list_cluster_members returns proper information.
        """
        bus = mock.MagicMock()
        bus.request.return_value = {
            'jsonrpc': '2.0',
            'result': Cluster.new(
                name='test', hostset=['127.0.0.1']).to_dict(secure=True),
            'id': '123'}
        self.assertEquals(
            {
                'jsonrpc': '2.0',
                'result': ['127.0.0.1'],
                'id': '123',
            },
            clusters.list_cluster_members({
                'jsonrpc': '2.0',
                'id': '123',
                'params': {'name': 'test'}
                }, bus))

    def test_update_cluster_members_with_valid_input(self):
        """
        Verify that update_cluster_members handles valid input.
        """
        bus = mock.MagicMock()
        cluster = Cluster.new(
            name='test', hostset=['127.0.0.1'])

        bus.request.return_value = {
            'jsonrpc': '2.0',
            'result': cluster.to_dict(secure=True),
            'id': '123'}

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

        bus.request.return_value = {
            'jsonrpc': '2.0',
            'result': cluster.to_dict(secure=True),
            'id': '123'}

        result = clusters.update_cluster_members({
            'jsonrpc': '2.0',
            'id': '123',
            'params': {'name': 'test', 'old': [], 'new': []}
        }, bus)

        expected_response =  create_response(
            id='123',
            error='Conflict setting hosts for cluster test',
            error_code=JSONRPC_ERRORS['CONFLICT'])
        self.assertEquals(expected_response, result)

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
                'id': '123',
                'params': params,
                }, mock.MagicMock())
            self.assertEquals(
                {
                    'jsonrpc': '2.0',
                    'error': {
                        'message': mock.ANY,
                        'code': JSONRPC_ERRORS['BAD_REQUEST'],
                        'data': {
                            'exception': "<class 'KeyError'>"
                        }
                    }, 'id': '123'
                },
                result
            )

    def test_check_cluster_member_with_valid_member(self):
        """
        Verify that check_cluster_member returns proper data when a valid member is requested.
        """
        bus = mock.MagicMock()
        cluster = Cluster.new(
            name='test', hostset=['127.0.0.1'])

        bus.request.return_value = {
            'jsonrpc': '2.0',
            'result': cluster.to_dict(secure=True),
            'id': '123'}

        result = clusters.check_cluster_member({
            'jsonrpc': '2.0',
            'id': '123',
            'params': {'name': 'test', 'host': '127.0.0.1'}
        }, bus)

        expected_response = create_response(
            '123', ['127.0.0.1'])
        self.assertEquals(expected_response, result)

    def test_check_cluster_member_with_invalid_member(self):
        """
        Verify that check_cluster_member returns proper data when an invalid member is requested.
        """
        bus = mock.MagicMock()
        cluster = Cluster.new(
            name='test', hostset=['127.0.0.1'])

        bus.request.return_value = {
            'jsonrpc': '2.0',
            'result': cluster.to_dict(secure=True),
            'id': '123'}

        result = clusters.check_cluster_member({
            'jsonrpc': '2.0',
            'id': '123',
            'params': {'name': 'test', 'host': '127.0.0.2'}
        }, bus)

        expected_response = create_response(
            '123',
            error='The requested host is not part of the cluster.',
            error_code=JSONRPC_ERRORS['NOT_FOUND'])
        self.assertEquals(expected_response, result)

    def test_add_cluster_member_with_valid_member(self):
        """
        Verify that add_cluster_member actually adds a new member..
        """
        bus = mock.MagicMock()
        cluster = Cluster.new(
            name='test', hostset=[])

        bus.request.return_value = {
            'jsonrpc': '2.0',
            'result': cluster.to_dict(secure=True),
            'id': '123'}

        result = clusters.add_cluster_member({
            'jsonrpc': '2.0',
            'id': '123',
            'params': {'name': 'test', 'host': '127.0.0.1'}
        }, bus)

        expected_response = create_response(
            '123', ['127.0.0.1'])
        self.assertEquals(expected_response, result)

    def test_delete_cluster_member_with_valid_member(self):
        """
        Verify that delete_cluster_member actually removes a member.
        """
        bus = mock.MagicMock()
        cluster = Cluster.new(
            name='test', hostset=['127.0.0.1'])

        bus.request.return_value = {
            'jsonrpc': '2.0',
            'result': cluster.to_dict(secure=True),
            'id': '123'}

        result = clusters.delete_cluster_member({
            'jsonrpc': '2.0',
            'id': '123',
            'params': {'name': 'test', 'host': '127.0.0.1'}
        }, bus)

        expected_response = create_response(
            '123', [])
        self.assertEquals(expected_response, result)
