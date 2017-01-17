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
Test for commissaire_http.handlers.container_managers module.
"""

from unittest import mock

from . import TestCase, expected_error

from commissaire import bus as _bus
from commissaire.constants import JSONRPC_ERRORS
from commissaire_http.handlers import (
    container_managers, create_jsonrpc_response)
from commissaire.models import ContainerManagerConfig, ContainerManagerConfigs

# Globals reused in network tests
#: Message ID
ID = '123'
#: Generic ContainerManagerConfig instance
CONTAINER_MANAGER_CONFIG = ContainerManagerConfig.new(name='test')
#: Generic jsonrpc network request by name
SIMPLE_CONTAINER_MANAGER_CONFIG_REQUEST = {
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


class Test_container_managers(TestCase):
    """
    Test for the container_managers handlers.
    """

    def test_list_container_managers(self):
        """
        Verify list_container_managers responds with the right information.
        """
        bus = mock.MagicMock()
        bus.storage.list.return_value = ContainerManagerConfigs.new(
            container_managers=[CONTAINER_MANAGER_CONFIG])
        self.assertEquals(
            create_jsonrpc_response(ID, ['test']),
            container_managers.list_container_managers(
                NO_PARAMS_REQUEST, bus))

    def test_get_container_manager(self):
        """
        Verify get_container_manager responds with the right information.
        """
        bus = mock.MagicMock()
        bus.storage.get.return_value = CONTAINER_MANAGER_CONFIG
        self.assertEquals(
            create_jsonrpc_response(ID, CONTAINER_MANAGER_CONFIG.to_dict()),
            container_managers.get_container_manager(
                SIMPLE_CONTAINER_MANAGER_CONFIG_REQUEST, bus))

    def test_get_missing_container_manager(self):
        """
        Verify get_container_manager responds with 404 when it does not exist.
        """
        bus = mock.MagicMock()
        bus.storage.get.side_effect = _bus.RemoteProcedureCallError('test')
        self.assertEquals(
            expected_error(ID, JSONRPC_ERRORS['NOT_FOUND']),
            container_managers.get_container_manager(
                SIMPLE_CONTAINER_MANAGER_CONFIG_REQUEST, bus))


    def test_create_container_manager(self):
        """
        Verify create_container_manager can create a new ContainerManagerConfig.
        """
        bus = mock.MagicMock()
        # ContainerManagerConfig doesn't yet exist
        bus.storage.get.side_effect = _bus.StorageLookupError(
            'test', CONTAINER_MANAGER_CONFIG)
        # Creation response
        bus.storage.save.return_value = CONTAINER_MANAGER_CONFIG
        self.assertEquals(
            create_jsonrpc_response(ID, CONTAINER_MANAGER_CONFIG.to_dict()),
            container_managers.create_container_manager(
                SIMPLE_CONTAINER_MANAGER_CONFIG_REQUEST, bus))

    def test_create_container_manager_idempotent(self):
        """
        Verify create_container_manager acts idempotent.
        """
        bus = mock.MagicMock()
        # ContainerManagerConfig exists
        bus.storage.get.return_value = CONTAINER_MANAGER_CONFIG
        # Creation response
        bus.storage.save.return_value = CONTAINER_MANAGER_CONFIG
        self.assertEquals(
            create_jsonrpc_response(ID, CONTAINER_MANAGER_CONFIG.to_dict()),
            container_managers.create_container_manager(
                SIMPLE_CONTAINER_MANAGER_CONFIG_REQUEST, bus))

    def test_create_container_manager_conflict(self):
        """
        Verify create_container_manager rejects conflicting creation.
        """
        bus = mock.MagicMock()
        bus.storage.get.return_value = ContainerManagerConfig.new(
            name=CONTAINER_MANAGER_CONFIG.name,
            options={'test': 'test'}
        )
        self.assertEquals(
            expected_error(ID, JSONRPC_ERRORS['CONFLICT']),
            container_managers.create_container_manager(
                SIMPLE_CONTAINER_MANAGER_CONFIG_REQUEST, bus))

    def test_delete_container_manager(self):
        """
        Verify delete_container_manager deletes existing ContainerManagerConfig.
        """
        bus = mock.MagicMock()
        bus.storage.delete.return_value = None
        self.assertEquals(
            {
                'jsonrpc': '2.0',
                'result': [],
                'id': '123',
            },
            container_managers.delete_container_manager(
                SIMPLE_CONTAINER_MANAGER_CONFIG_REQUEST, bus))

    def test_delete_container_manager_not_found_on_missing_key(self):
        """
        Verify delete_container_manager returns 404 on a missing ContainerManagerConfig.
        """
        bus = mock.MagicMock()
        bus.storage.delete.side_effect = _bus.RemoteProcedureCallError('test')

        self.assertEquals(
            expected_error(ID, JSONRPC_ERRORS['NOT_FOUND']),
            container_managers.delete_container_manager(
                SIMPLE_CONTAINER_MANAGER_CONFIG_REQUEST, bus))

    def test_delete_container_manager_internal_error_on_exception(self):
        """
        Verify delete_container_manager returns ISE on any other exception
        """
        # Iterate over a few errors
        for error in (Exception, KeyError, TypeError):
            bus = mock.MagicMock()
            bus.storage.delete.side_effect = error('test')

            self.assertEquals(
                expected_error(ID, JSONRPC_ERRORS['INTERNAL_ERROR']),
                container_managers.delete_container_manager(
                    SIMPLE_CONTAINER_MANAGER_CONFIG_REQUEST, bus))
