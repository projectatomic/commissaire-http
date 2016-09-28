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


# NOTE: commenting out etcd related loading until we have the storage
#       service
#import etcd

from . import TestCase, create_environ, get_fixture_file_path

from unittest import mock
from commissaire_http.authentication import httpbasicauth
from commissaire_http.authentication import httpauthclientcert


class Test_HTTPBasicAuth(TestCase):
    """
    Tests for the _HTTPBasicAuth class.
    """

    def setUp(self):
        """
        Sets up a fresh instance of the class before each run.
        """
        # Empty users dict prevents it from trying to load from etcd.
        self.http_basic_auth = httpbasicauth.HTTPBasicAuth(None, users={})

    def test_decode_basic_auth(self):
        """
        Verify decoding returns a filled tuple given the proper header no matter the case of basic.
        """
        basic = list('basic')
        for x in range(0, 5):
            self.assertEquals(
                ('a', 'a'),
                self.http_basic_auth._decode_basic_auth(
                    '{0} YTph'.format(''.join(basic))))
            # Update the next letter to be capitalized
            basic[x] = basic[x].capitalize()

    def test_decode_basic_auth_with_bad_data(self):
        """
        Verify decoding returns no user with bad base64 data in the header.
        """
        self.assertEquals(
            (None, None),
            self.http_basic_auth._decode_basic_auth('basic BADDATA'))


class TestHTTPBasicAuthByFile(TestCase):
    """
    Tests for the HTTPBasicAuth class using files.
    """

    def setUp(self):
        """
        Sets up a fresh instance of the class before each run.
        """
        self.user_config = get_fixture_file_path('conf/users.json')
        self.http_basic_auth = httpbasicauth.HTTPBasicAuth(self.user_config)

    def test_load_with_non_parsable_file(self):
        """
        Verify load gracefully loads no users when the JSON file does not exist or is malformed.
        """
        for bad_file in ('', get_fixture_file_path('test/bad.json')):
            self.http_basic_auth._data = {}
            self.http_basic_auth._load_from_file(bad_file)
            self.assertEquals(
                {},
                self.http_basic_auth._data
            )

    def test_authenticate_with_valid_user(self):
        """
        Verify authenticate works with a proper JSON file, Authorization header, and a matching user.
        """
        self.http_basic_auth = httpbasicauth.HTTPBasicAuth(None, self.user_config)
        environ = create_environ(headers={'HTTP_AUTHORIZATION': 'basic YTph'})
        self.assertEquals(
            True,
            self.http_basic_auth.authenticate(environ, mock.MagicMock()))

    def test_authenticate_with_invalid_user(self):
        """
        Verify authenticate denies with a proper JSON file, Authorization header, and no matching user.
        """
        self.http_basic_auth = httpbasicauth.HTTPBasicAuth(None, self.user_config)
        environ = create_environ(headers={'HTTP_AUTHORIZATION': 'basic Yjpi'})

        self.assertEquals(
            False,
            self.http_basic_auth.authenticate(environ, mock.MagicMock()))

    def test_authenticate_with_invalid_password(self):
        """
        Verify authenticate denies with a proper JSON file, Authorization header, and the wrong password.
        """
        self.http_basic_auth= httpbasicauth.HTTPBasicAuth(None, self.user_config)
        environ = create_environ(headers={'HTTP_AUTHORIZATION': 'basic YTpiCg=='})
        self.assertEquals(
            False,
            self.http_basic_auth.authenticate(environ, mock.MagicMock()))


'''
class TestHTTPBasicAuthByEtcd(TestCase):
    """
    Tests for the HTTPBasicAuth class using etcd.
    """

    def setUp(self):
        """
        Sets up a fresh instance of the class before each run.
        """
        self.user_config = get_fixture_file_path('conf/users.json')

    def test_load_with_non_key(self):
        """
        Verify load raises when the key does not exist in etcd.
        """
        with mock.patch('cherrypy.engine.publish') as _publish:
            manager = mock.MagicMock(StoreHandlerManager)
            _publish.return_value = [manager]

            manager.get.side_effect = etcd.EtcdKeyNotFound

            self.assertRaises(
                etcd.EtcdKeyNotFound,
                httpbasicauth.HTTPBasicAuth)

    def test_load_with_bad_data(self):
        """
        Verify load raises when the data in Etcd is bad.
        """
        with mock.patch('cherrypy.engine.publish') as _publish:
            manager = mock.MagicMock(StoreHandlerManager)
            _publish.return_value = [manager]

            manager.get.side_effect = ValueError

            self.assertRaises(
                ValueError,
                httpbasicauth.HTTPBasicAuth)

    def test_authenticate_with_valid_user(self):
        """
        Verify authenticate works with a proper JSON in Etcd, Authorization header, and a matching user.
        """
        with mock.patch('cherrypy.engine.publish') as _publish:
            # Mock the return of the Etcd get result
            return_value = mock.MagicMock(etcd.EtcdResult)
            with open(self.user_config, 'r') as users_file:
                return_value.value = users_file.read()

            manager = mock.MagicMock(StoreHandlerManager)
            _publish.return_value = [manager]

            manager.get.return_value = return_value

            # Reload with the data from the mock'd Etcd
            http_basic_auth = httpbasicauth.HTTPBasicAuth(None)

            # Test the call
            req = falcon.Request(
                create_environ(headers={'Authorization': 'basic YTph'}))
            resp = falcon.Response()
            self.assertEquals(
                None,
                http_basic_auth.authenticate(req, resp))

    def test_authenticate_with_invalid_user(self):
        """
        Verify authenticate denies with a proper JSON in Etcd, Authorization header, and no matching user.
        """
        with mock.patch('cherrypy.engine.publish') as _publish:
            # Mock the return of the Etcd get result
            return_value = mock.MagicMock(etcd.EtcdResult)
            with open(self.user_config, 'r') as users_file:
                return_value.value = users_file.read()

            manager = mock.MagicMock(StoreHandlerManager)
            _publish.return_value = [manager]

            manager.get.return_value = return_value

            # Reload with the data from the mock'd Etcd
            http_basic_auth = httpbasicauth.HTTPBasicAuth(None)

            # Test the call
            req = falcon.Request(
                create_environ(headers={'Authorization': 'basic Yjpi'}))
            resp = falcon.Response()
            self.assertRaises(
                falcon.HTTPForbidden,
                http_basic_auth.authenticate,
                req, resp)

    def test_authenticate_with_invalid_password(self):
        """
        Verify authenticate denies with a proper JSON file, Authorization header, and the wrong password.
        """
        with mock.patch('cherrypy.engine.publish') as _publish:
            return_value = mock.MagicMock(etcd.EtcdResult)
            with open(self.user_config, 'r') as users_file:
                return_value.value = users_file.read()

            manager = mock.MagicMock(StoreHandlerManager)
            _publish.return_value = [manager]

            manager.get.return_value = return_value

            # Reload with the data from the mock'd Etcd
            http_basic_auth = httpbasicauth.HTTPBasicAuth(None)

            req = falcon.Request(
                create_environ(headers={'Authorization': 'basic YTpiCg=='}))
            resp = falcon.Response()
            self.assertRaises(
                falcon.HTTPForbidden,
                http_basic_auth.authenticate,
                req, resp)
'''
