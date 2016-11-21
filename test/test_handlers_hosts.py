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
Test for commissaire_http.handlers.hosts module.
"""
import copy

from unittest import mock

from . import TestCase, expected_error

from commissaire import bus as _bus
from commissaire import constants as C
from commissaire.constants import JSONRPC_ERRORS
from commissaire_http.handlers import hosts, create_response, clusters
from commissaire.models import Host, HostStatus, ValidationError

# Globals reused in host tests
#: Message ID
ID = '123'
#: Generic host instance
HOST = Host.new(address='127.0.0.1')
#: Generic jsonrpc host request by address
SIMPLE_HOST_REQUEST = {
    'jsonrpc': '2.0',
    'id': ID,
    'params': HOST.to_dict(),
}
CLUSTER_HOST_REQUEST = {
    'jsonrpc': '2.0',
    'id': ID,
    'params': {
        'address': HOST.address,
        'cluster': 'mycluster',
    },
}


class Test_hosts(TestCase):
    """
    Test for the Hosts handlers.
    """

    def test_list_hosts(self):
        """
        Verify list_hosts responds with the right information.
        """
        bus = mock.MagicMock()
        bus.request.return_value = {
            'jsonrpc': '2.0',
            'result': [HOST.to_dict()],
            'id': '123'}
        self.assertEquals(
            create_response(ID, [HOST.to_dict()]),
            hosts.list_hosts(SIMPLE_HOST_REQUEST, bus))

    def test_get_host(self):
        """
        Verify get_host responds with the right information.
        """
        bus = mock.MagicMock()
        bus.request.return_value = create_response(ID, HOST.to_dict())
        self.assertEquals(
            create_response(ID, HOST.to_dict()),
            hosts.get_host(SIMPLE_HOST_REQUEST, bus))

    def test_get_host_that_doesnt_exist(self):
        """
        Verify get_host responds with a 404 error on missing hosts.
        """
        bus = mock.MagicMock()
        bus.request.side_effect = _bus.RemoteProcedureCallError('test')

        self.assertEquals(
            expected_error(ID, JSONRPC_ERRORS['NOT_FOUND']),
            hosts.get_host(SIMPLE_HOST_REQUEST, bus))

    def test_create_host(self):
        """
        Verify create_host saves new hosts.
        """
        bus = mock.MagicMock()
        bus.request.side_effect = (
            # Host doesn't exist yet
            _bus.RemoteProcedureCallError('test'),
            # Result from save
            create_response(ID, HOST.to_dict())
        )

        self.assertEquals(
            create_response(ID, HOST.to_dict_safe()),
            hosts.create_host(SIMPLE_HOST_REQUEST, bus))

    def test_create_host_without_an_address(self):
        """
        Verify create_host returns INVALID_PARAMETERS when no address is given.
        """
        bus = mock.MagicMock()
        bus.request.side_effect = (
            # Host doesn't exist yet
            _bus.RemoteProcedureCallError('test'),
            # Result from save
            create_response(ID, HOST.to_json())
        )

        addressless = copy.deepcopy(SIMPLE_HOST_REQUEST)
        addressless['params'] = {}

        self.assertEquals(
            expected_error(ID, JSONRPC_ERRORS['INVALID_PARAMETERS']),
            hosts.create_host(addressless, bus))


    def test_create_host_with_invalid_cluster(self):
        """
        Verify create_host returns INVALID_PARAMETERS when the cluster does not exist.
        """
        bus = mock.MagicMock()

        bus.request.side_effect = (
            # Host doesn't exist yet
            _bus.RemoteProcedureCallError('test'),
            # Request the cluster which does not exist
            _bus.RemoteProcedureCallError('test')
        )

        self.assertEquals(
            expected_error(ID, JSONRPC_ERRORS['INVALID_PARAMETERS']),
            hosts.create_host(CLUSTER_HOST_REQUEST, bus))

    def test_create_host_with_cluster(self):
        """
        Verify create_host saves new hosts with it's cluster.
        """
        bus = mock.MagicMock()

        bus.request.side_effect = (
            # Host doesn't exist yet
            _bus.RemoteProcedureCallError('test'),
            # Request the cluster
            create_response(ID, {'hostset': []}),
            # Save of the cluster
            create_response(ID, {'hostset': []}),
            # Result from save (ignored)
            create_response(ID, HOST.to_dict())
        )

        self.assertEquals(
            create_response(ID, HOST.to_dict_safe()),
            hosts.create_host(CLUSTER_HOST_REQUEST, bus))

    def test_create_host_with_the_same_existing_host(self):
        """
        Verify create_host succeeds when a new host matches an existing one.
        """
        bus = mock.MagicMock()
        bus.request.side_effect = (
            # Existing host
            create_response(ID, HOST.to_dict()),
            # Result from save
            create_response(ID, HOST.to_dict())
        )

        self.assertEquals(
            create_response(ID, HOST.to_dict_safe()),
            hosts.create_host(SIMPLE_HOST_REQUEST, bus))

    def test_create_host_with_existing_host_different_ssh_key(self):
        """
        Verify create_host returns conflict existing hosts ssh keys do not match.
        """
        bus = mock.MagicMock()
        different = HOST.to_dict()
        different['ssh_priv_key'] = 'aaa'

        bus.request.return_value = create_response(ID, different)

        self.assertEquals(
            expected_error(ID, JSONRPC_ERRORS['CONFLICT']),
            hosts.create_host(SIMPLE_HOST_REQUEST, bus))

    def test_create_host_with_existing_host_different_cluster_memebership(self):
        """
        Verify create_host returns conflict existing cluster memebership does not match.
        """
        bus = mock.MagicMock()
        different = HOST.to_dict()
        different['ssh_priv_key'] = ''

        bus.request.side_effect = (
            # Existing host
            create_response(ID, different),
            # Cluster
            create_response(ID, {'hostset': []}),
            create_response(ID, {'hostset': []})
        )

        self.assertEquals(
            expected_error(ID, JSONRPC_ERRORS['CONFLICT']),
            hosts.create_host(CLUSTER_HOST_REQUEST, bus))

    def test_delete_host(self):
        """
        Verify delete_host deletes existing hosts.
        """
        bus = mock.MagicMock()
        bus.request.side_effect = (
            # The delete shouldn't return anything
            None,
            # The clusters list
            {'result': [{'hostset': []}]},
        )
        self.assertEquals(
            {
                'jsonrpc': '2.0',
                'result': [],
                'id': '123',
            },
            hosts.delete_host(SIMPLE_HOST_REQUEST, bus))

    def test_delete_host_thats_in_a_cluster(self):
        """
        Verify delete_host deletes existing host and removes it from it's cluster.
        """
        bus = mock.MagicMock()
        bus.request.side_effect = (
            # The delete shouldn't return anything
            None,
            # The clusters list
            {'result': [{'name': 'mycluster', 'hostset': [HOST.address]}]},
            # The cluster response on save (which is ignored)
            {'result': []}
        )
        self.assertEquals(
            {
                'jsonrpc': '2.0',
                'result': [],
                'id': '123',
            },
            hosts.delete_host(SIMPLE_HOST_REQUEST, bus))

        # Verify we had a host delete_host
        bus.request.assert_has_calls((
            # Verify we had an initial delete
            mock.call('storage.delete', params=[
                'Host', {'address': HOST.address}]),
            # Verify we had a list of clusters
            mock.call('storage.list', params=['Clusters', True]),
            # Verify we had a cluster save
            mock.call('storage.save', params=['Cluster', mock.ANY])
        ))

    def test_delete_host_not_found_on_missing_key(self):
        """
        Verify delete_host returns 404 on a missing host.
        """
        bus = mock.MagicMock()
        bus.request.side_effect = _bus.RemoteProcedureCallError('test')

        self.assertEquals(
            expected_error(ID, JSONRPC_ERRORS['NOT_FOUND']),
            hosts.delete_host(SIMPLE_HOST_REQUEST, bus))

    def test_delete_host_internal_error_on_exception(self):
        """
        Verify delete_host returns ISE on any other exception
        """
        # Iterate over a few errors
        for error in (Exception, KeyError, TypeError):
            bus = mock.MagicMock()
            bus.request.side_effect = error('test')

            self.assertEquals(
                expected_error(ID, JSONRPC_ERRORS['INTERNAL_ERROR']),
                hosts.delete_host(SIMPLE_HOST_REQUEST, bus))

    def test_get_host_creds(self):
        """
        Verify get_hostcreds responds with the right information.
        """
        bus = mock.MagicMock()
        bus.request.return_value = create_response(ID, HOST.to_dict())
        self.assertEquals(
            create_response(ID, {'ssh_priv_key': '', 'remote_user': 'root'}),
            hosts.get_hostcreds(SIMPLE_HOST_REQUEST, bus))

    def test_get_hostcreds_that_doesnt_exist(self):
        """
        Verify get_hostcreds responds with a 404 error on missing hosts.
        """
        bus = mock.MagicMock()
        bus.request.side_effect = _bus.RemoteProcedureCallError('test')

        self.assertEquals(
            expected_error(ID, JSONRPC_ERRORS['NOT_FOUND']),
            hosts.get_hostcreds(SIMPLE_HOST_REQUEST, bus))

    def test_get_host_status(self):
        """
        Verify get_host_status responds with status information.
        """
        bus = mock.MagicMock()
        bus.request.return_value = create_response(ID, HOST.to_dict())
        host_status = HostStatus.new(
            host={'last_check': '', 'status': ''}, type='host_only')
        self.assertEquals(
            create_response(ID, host_status.to_dict()),
            hosts.get_host_status(SIMPLE_HOST_REQUEST, bus))

    def test_get_host_status_that_doesnt_exist(self):
        """
        Verify get_host_status responds with a 404 error on missing hosts.
        """
        bus = mock.MagicMock()
        bus.request.side_effect = _bus.RemoteProcedureCallError('test')

        self.assertEquals(
            expected_error(ID, JSONRPC_ERRORS['NOT_FOUND']),
            hosts.get_host_status(SIMPLE_HOST_REQUEST, bus))
