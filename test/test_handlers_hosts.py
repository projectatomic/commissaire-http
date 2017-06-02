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
from commissaire_http.handlers import hosts, create_jsonrpc_response, clusters
from commissaire.models import (
    Host, Hosts, HostCreds, HostStatus, Cluster, Clusters, ValidationError)

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
HOST_CREDS = {
    'address': '127.0.0.1',
    'ssh_priv_key': '',
    'remote_user': 'root',
}
HTTP_HOST_REQUEST = HOST.to_dict()
HTTP_HOST_REQUEST.update(HOST_CREDS)
CLUSTER_HOST_REQUEST = {
    'jsonrpc': '2.0',
    'id': ID,
    'params': {
        'address': HOST.address,
        'cluster': 'mycluster',
        'ssh_priv_key': '',
        'remote_user': 'root',
    },
}
#: Generic jsonrpc request with no parameters
NO_PARAMS_REQUEST = {
    'jsonrpc': '2.0',
    'id': ID,
    'params': {}
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
        bus.storage.list.return_value = Hosts.new(hosts=[HOST])
        self.assertEquals(
            create_jsonrpc_response(ID, [HOST.to_dict_safe()]),
            hosts.list_hosts.handler(NO_PARAMS_REQUEST, bus))

    def test_get_host(self):
        """
        Verify get_host responds with the right information.
        """
        bus = mock.MagicMock()
        bus.storage.get_host.return_value = HOST
        self.assertEquals(
            create_jsonrpc_response(ID, HOST.to_dict_safe()),
            hosts.get_host.handler(SIMPLE_HOST_REQUEST, bus))

    def test_get_host_that_doesnt_exist(self):
        """
        Verify get_host responds with a 404 error on missing hosts.
        """
        bus = mock.MagicMock()
        bus.storage.get_host.side_effect = _bus.RemoteProcedureCallError('test')

        self.assertEquals(
            expected_error(ID, JSONRPC_ERRORS['NOT_FOUND']),
            hosts.get_host.handler(SIMPLE_HOST_REQUEST, bus))

    def test_create_host(self):
        """
        Verify create_host saves new hosts.
        """
        bus = mock.MagicMock()
        # Host doesn't exist yet
        bus.storage.get_host.side_effect = _bus.RemoteProcedureCallError('test')
        # Result from save
        bus.storage.save.return_value = HOST

        self.assertEquals(
            create_jsonrpc_response(ID, HOST.to_dict_safe()),
            hosts.create_host.handler(SIMPLE_HOST_REQUEST, bus))

    def test_create_host_without_an_address(self):
        """
        Verify create_host returns INVALID_PARAMETERS when no address is given.
        """
        bus = mock.MagicMock()
        # Host doesn't exist yet
        bus.storage.get.side_effect = _bus.RemoteProcedureCallError('test')
        # Result from save
        bus.storage.save.return_value = HOST

        addressless = copy.deepcopy(SIMPLE_HOST_REQUEST)
        addressless['params'] = {}

        self.assertEquals(
            expected_error(ID, JSONRPC_ERRORS['INVALID_PARAMETERS']),
            hosts.create_host.handler(addressless, bus))

    def test_create_host_with_invalid_cluster(self):
        """
        Verify create_host returns INVALID_PARAMETERS when the cluster does not exist.
        """
        bus = mock.MagicMock()
        bus.storage.get.side_effect = (
            # Host doesn't exist yet
            _bus.RemoteProcedureCallError('test'),
        )

        bus.storage.get_cluster.side_effect = (
            # Request the cluster which does not exist
            _bus.StorageLookupError('Not found'),
        )

        self.assertEquals(
            expected_error(ID, JSONRPC_ERRORS['INVALID_PARAMETERS']),
            hosts.create_host.handler(CLUSTER_HOST_REQUEST, bus))

    def test_create_host_with_cluster(self):
        """
        Verify create_host saves new hosts with it's cluster.
        """
        bus = mock.MagicMock()

        # Host doesn't exist yet
        bus.storage.get_host.side_effect = _bus.RemoteProcedureCallError('test')
        # Request the cluster
        bus.storage.get_cluster.return_value = Cluster.new(name='mycluster')
        bus.storage.save.side_effect = (
            # Cluster save (ignored)
            None,
            # Creds, not used in this test
            None,
            # Result from save
            HOST
        )

        self.assertEquals(
            create_jsonrpc_response(ID, HOST.to_dict_safe()),
            hosts.create_host.handler(CLUSTER_HOST_REQUEST, bus))

    def test_create_host_with_the_same_existing_host(self):
        """
        Verify create_host succeeds when a new host matches an existing one.
        """
        bus = mock.MagicMock()
        # Existing host
        bus.storage.get_host.return_value = HOST
        # Existing creds
        bus.storage.get.return_value = HostCreds(**HOST_CREDS)
        # Result from save
        bus.storage.save.return_value = HOST

        self.assertEquals(
            create_jsonrpc_response(ID, HOST.to_dict_safe()),
            hosts.create_host.handler(SIMPLE_HOST_REQUEST, bus))

    def test_create_host_with_existing_host_different_ssh_key(self):
        """
        Verify create_host returns conflict existing hosts ssh keys do not match.
        """
        bus = mock.MagicMock()
        different = Host.new(**HOST.to_dict())
        different.ssh_priv_key = 'aaa'

        bus.storage.save.return_value = different

        self.assertEquals(
            expected_error(ID, JSONRPC_ERRORS['CONFLICT']),
            hosts.create_host.handler(SIMPLE_HOST_REQUEST, bus))

    def test_create_host_with_existing_host_different_cluster_memebership(self):
        """
        Verify create_host returns conflict existing cluster memebership does not match.
        """
        bus = mock.MagicMock()
        different = HOST.to_dict()
        different['ssh_priv_key'] = ''

        # Existing host
        bus.storage.get_host.return_value = Host.new(**different)
        bus.storage.get.return_value = HostCreds.new(**HOST_CREDS)

        # Cluster
        bus.storage.get_cluster.return_value = Cluster.new(name='test')

        self.assertEquals(
            expected_error(ID, JSONRPC_ERRORS['CONFLICT']),
            hosts.create_host.handler(CLUSTER_HOST_REQUEST, bus))

    def test_delete_host(self):
        """
        Verify delete_host deletes existing hosts.
        """
        bus = mock.MagicMock()
        # The delete shouldn't return anything
        bus.storage.delete.return_value = None
        bus.storage.list.return_value = Clusters.new(
            clusters=[Cluster.new(name='test')])
        self.assertEquals(
            {
                'jsonrpc': '2.0',
                'result': [],
                'id': '123',
            },
            hosts.delete_host.handler(SIMPLE_HOST_REQUEST, bus))

    def test_delete_host_thats_in_a_cluster(self):
        """
        Verify delete_host deletes existing host and removes it from its cluster.
        """
        bus = mock.MagicMock()
        # The delete shouldn't return anything
        bus.storage.delete.return_value = None
        # The cluster response on save (which is ignored)
        bus.storage.save.return_value = None
        # The clusters list
        bus.storage.list.return_value = Clusters.new(
            clusters=[Cluster.new(name='mycluster', hostset=[HOST.address])])
        self.assertEquals(
            {
                'jsonrpc': '2.0',
                'result': [],
                'id': '123',
            },
            hosts.delete_host.handler(SIMPLE_HOST_REQUEST, bus))

        # Verify we had a host delete_host
        bus.storage.delete.assert_called_with(mock.ANY)
        # Verify we had a list of clusters
        bus.storage.list.assert_called_with(Clusters)
        # Verify we did NOT have a 'container.remove_node'
        # XXX Fragile; will break if another bus.request call is added.
        bus.request.assert_not_called()
        # Verify we had a cluster save
        bus.storage.save.assert_called_with(mock.ANY)

    def test_delete_host_thats_in_a_container_manager(self):
        """
        Verify delete_host deletes existing host and removes it from its cluster
        and container manager.
        """
        bus = mock.MagicMock()
        # The delete shouldn't return anything
        bus.storage.delete.return_value = None
        # The cluster response on save (which is ignored)
        bus.storage.save.return_value = None
        # The clusters list
        bus.storage.list.return_value = Clusters.new(
            clusters=[Cluster.new(
                name='mycluster',
                hostset=[HOST.address],
                container_manager='test')])
        self.assertEquals(
            {
                'jsonrpc': '2.0',
                'result': [],
                'id': '123',
            },
            hosts.delete_host.handler(SIMPLE_HOST_REQUEST, bus))

        # Verify we had a host delete_host
        bus.storage.delete.assert_called_with(mock.ANY)
        # Verify we had a list of clusters
        bus.storage.list.assert_called_with(Clusters)
        # Verify we had a 'container.remove_node'
        bus.request.assert_called_with('container.remove_node', params=mock.ANY)
        # Verify we had a cluster save
        bus.storage.save.assert_called_with(mock.ANY)

    def test_delete_host_not_found_on_missing_key(self):
        """
        Verify delete_host returns 404 on a missing host.
        """
        bus = mock.MagicMock()
        bus.storage.delete.side_effect = _bus.RemoteProcedureCallError('test')

        self.assertEquals(
            expected_error(ID, JSONRPC_ERRORS['NOT_FOUND']),
            hosts.delete_host.handler(SIMPLE_HOST_REQUEST, bus))

    def test_delete_host_internal_error_on_exception(self):
        """
        Verify delete_host returns ISE on any other exception
        """
        # Iterate over a few errors
        for error in (Exception, KeyError, TypeError):
            bus = mock.MagicMock()
            bus.storage.delete.side_effect = error('test')

            self.assertEquals(
                expected_error(ID, JSONRPC_ERRORS['INTERNAL_ERROR']),
                hosts.delete_host.handler(SIMPLE_HOST_REQUEST, bus))

    def test_get_host_creds(self):
        """
        Verify get_hostcreds responds with the right information.
        """
        bus = mock.MagicMock()
        bus.storage.get.return_value = HostCreds.new(**HOST_CREDS)
        self.assertEquals(
            create_jsonrpc_response(ID, HOST_CREDS),
            hosts.get_hostcreds.handler(SIMPLE_HOST_REQUEST, bus))

    def test_get_hostcreds_that_doesnt_exist(self):
        """
        Verify get_hostcreds responds with a 404 error on missing hosts.
        """
        bus = mock.MagicMock()
        bus.storage.get.side_effect = _bus.RemoteProcedureCallError('test')

        self.assertEquals(
            expected_error(ID, JSONRPC_ERRORS['NOT_FOUND']),
            hosts.get_hostcreds.handler(SIMPLE_HOST_REQUEST, bus))

    def test_get_host_status(self):
        """
        Verify get_host_status responds with status information.
        """
        bus = mock.MagicMock()
        bus.storage.get_host.return_value = HOST
        host_status = HostStatus.new(
            host={'last_check': '', 'status': ''}, type='host_only')
        self.assertEquals(
            create_jsonrpc_response(ID, host_status.to_dict()),
            hosts.get_host_status.handler(SIMPLE_HOST_REQUEST, bus))

    def test_get_host_status_with_container_manager(self):
        """
        Verify get_host status includes container manager status
        """
        bus = mock.MagicMock()
        bus.storage.get_host.return_value = HOST

        cluster = Cluster.new(
            name='test', hostset=['127.0.0.1'],
            container_manager='trivial')
        bus.storage.list.return_value = Clusters.new(clusters=[cluster])

        # XXX Fragile; will break if another bus.request call is added.
        bus.request.return_value = {'status': 'ok'}

        host_status = HostStatus.new(
            host={'last_check': '', 'status': ''}, type='host_only',
            container_manager={'status': 'ok'})
        self.assertEquals(
            create_jsonrpc_response(ID, host_status.to_dict()),
            hosts.get_host_status.handler(SIMPLE_HOST_REQUEST, bus))

    def test_get_host_status_that_doesnt_exist(self):
        """
        Verify get_host_status responds with a 404 error on missing hosts.
        """
        bus = mock.MagicMock()
        bus.storage.get_host.side_effect = _bus.RemoteProcedureCallError('test')

        self.assertEquals(
            expected_error(ID, JSONRPC_ERRORS['NOT_FOUND']),
            hosts.get_host_status.handler(SIMPLE_HOST_REQUEST, bus))
