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
Test cases for the commissaire_http.authentication package.
"""

from unittest import mock

from . import TestCase, create_environ, get_fixture_file_path

from commissaire_http.authentication import httpbasicauth
from commissaire_http.authentication import httpauthclientcert


class TestHTTPClientCertAuth(TestCase):
    """
    Tests for the HTTPBasicAuthByEtcd class.
    """

    def setUp(self):
        self.cert = {
            "version": 3,
            "notAfter": "Apr 11 08:32:52 2018 GMT",
            "notBefore": "Apr 11 08:32:51 2016 GMT",
            "serialNumber": "07",
            "subject": [
                [["organizationName", "system:master"]],
                [["commonName", "system:master-proxy"]]],
            "issuer": [
                [["commonName", "openshift-signer@1460363571"]]
             ]
        }

    def expect_forbidden(self, data=None, cn=None):
        auth = httpauthclientcert.HTTPClientCertAuth(cn=cn)
        environ = create_environ()
        if data is not None:
            environ['SSL_CLIENT_VERIFY'] = data

        self.assertFalse(auth.authenticate(environ, mock.MagicMock()))

    def test_invalid_certs(self):
        """
        Verify authenticate denies when cert is missing or invalid
        """
        self.expect_forbidden()
        self.expect_forbidden(data={"bad": "data"})
        self.expect_forbidden(data={"subject": (("no", "cn"),)})

    def test_valid_certs(self):
        """
        Verify authenticate succeeds when cn matches, fails when it doesn't
        """
        self.expect_forbidden(data=self.cert, cn="other-cn")

        auth = httpauthclientcert.HTTPClientCertAuth(cn="system:master-proxy")
        environ = create_environ()
        environ['SSL_CLIENT_VERIFY'] = self.cert
        self.assertTrue(auth.authenticate(environ, mock.MagicMock()))

        # With no cn any is valid
        auth = httpauthclientcert.HTTPClientCertAuth()
        self.assertTrue(auth.authenticate(environ, mock.MagicMock()))
