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

from . import TestCase

from commissaire.constants import JSONRPC_ERRORS
from commissaire_http.handlers import create_response, clusters
from commissaire.models import Network, ValidationError


class Test_networks(TestCase):
    """
    Test for the networks handlers.
    """

    def test_list_networks(self):
        """
        Verify list_networks responds with the right information.
        """
        bus = mock.MagicMock()
        bus.request.return_value = {
            'jsonrpc': '2.0',
            'result': [Network.new(name='test').to_dict()],
            'id': '123'}
        self.assertEquals(
            {
                'jsonrpc': '2.0',
                'result': ['test'],
                'id': '123',
            },
            clusters.list_clusters(bus.request.return_value, bus))
