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
Constants specific to the HTTP related code.
"""

from commissaire.constants import JSONRPC_ERRORS

# Add HTTP view to JSONRPC_ERRORS
JSONRPC_ERRORS['404'] = JSONRPC_ERRORS['NOT_FOUND']
JSONRPC_ERRORS['400'] = JSONRPC_ERRORS['INVALID_REQUEST']
JSONRPC_ERRORS['BAD_REQUEST'] = JSONRPC_ERRORS['INVALID_REQUEST']

ROUTING_RX_PARAMS = {
    'name': R'[a-zA-Z0-9\-\_]+',
    'host': R'[a-zA-Z0-9\-\_\.]+',
    'address': R'[a-zA-Z0-9\-\_\.]+',
}
