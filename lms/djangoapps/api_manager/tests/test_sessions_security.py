"""
Tests for session api with advance security features
"""
import json
import uuid
import unittest
from mock import patch
from datetime import datetime, timedelta
from freezegun import freeze_time
from pytz import UTC

from django.test import TestCase
from django.test.client import Client
from django.test.utils import override_settings
from django.utils.translation import ugettext as _
from django.conf import settings
from django.core.cache import cache
from student.tests.factories import UserFactory

TEST_API_KEY = str(uuid.uuid4())


@override_settings(EDX_API_KEY=TEST_API_KEY)
@patch.dict("django.conf.settings.FEATURES", {'ENFORCE_PASSWORD_POLICY': True})
@patch.dict("django.conf.settings.FEATURES", {'ENABLE_MAX_FAILED_LOGIN_ATTEMPTS': True})
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class SessionApiSecurityTest(TestCase):
    """
    Test api_manager.session.session_list view
    """

    def setUp(self):
        """
        Create one user and save it to the database
        """
        self.user = UserFactory.build(username='test', email='test@edx.org')
        self.user.set_password('test_password')
        self.user.save()

        # Create the test client
        self.client = Client()
        cache.clear()
        self.session_url = '/api/sessions'
        self.user_url = '/api/users'

    @override_settings(ENABLE_MAX_FAILED_LOGIN_ATTEMPTS=True, MAX_FAILED_LOGIN_ATTEMPTS_ALLOWED=10)
    def test_login_ratelimited_success(self):
        """
        Try (and fail) logging in with fewer attempts than the limit of 10
        and verify that you can still successfully log in afterwards.
        """
        for i in xrange(9):
            password = u'test_password{0}'.format(i)
            response = self._do_post_request(self.session_url, 'test', password, secure=True)
            self.assertEqual(response.status_code, 401)

        # now try logging in with a valid password and check status
        response = self._do_post_request(self.session_url, 'test', 'test_password', secure=True)
        self._assert_response(response, status=201)

    @override_settings(ENABLE_MAX_FAILED_LOGIN_ATTEMPTS=True, MAX_FAILED_LOGIN_ATTEMPTS_ALLOWED=10)
    def test_login_blockout(self):
        """
        Try (and fail) logging in with 10 attempts
        and verify that user is blocked out.
        """
        for i in xrange(10):
            password = u'test_password{0}'.format(i)
            response = self._do_post_request(self.session_url, 'test', password, secure=True)
            self.assertEqual(response.status_code, 401)

        # check to see if this response indicates blockout
        response = self._do_post_request(self.session_url, 'test', 'test_password', secure=True)
        message = _('This account has been temporarily locked due to excessive login failures. Try again later.')
        self._assert_response(response, status=403, message=message)

    @override_settings(ENABLE_MAX_FAILED_LOGIN_ATTEMPTS=True, MAX_FAILED_LOGIN_ATTEMPTS_ALLOWED=10,
                       MAX_FAILED_LOGIN_ATTEMPTS_LOCKOUT_PERIOD_SECS=1800)
    def test_blockout_reset_time_period(self):
        """
        Try logging in 10 times to block user and then login with right
        credentials(after 30 minutes) to verify blocked out time expired and
        user can login successfully.
        """
        for i in xrange(10):
            password = u'test_password{0}'.format(i)
            response = self._do_post_request(self.session_url, 'test', password, secure=True)
            self.assertEqual(response.status_code, 401)

        # check to see if this response indicates blockout
        response = self._do_post_request(self.session_url, 'test', 'test_password', secure=True)
        message = _('This account has been temporarily locked due to excessive login failures. Try again later.')
        self._assert_response(response, status=403, message=message)

        # now reset the time to 30 from now in future
        reset_time = datetime.now(UTC) + timedelta(seconds=1800)
        with freeze_time(reset_time):
            response = self._do_post_request(self.session_url, 'test', 'test_password', secure=True)
            self._assert_response(response, status=201)

    @override_settings(ENFORCE_PASSWORD_POLICY=True, PASSWORD_MIN_LENGTH=4)
    def test_with_short_password(self):
        """
        Try (and fail) user creation with shorter password
        """
        response = self._do_post_request(self.user_url, 'test', 'abc', email='test@edx.org',
                                         first_name='John', last_name='Doe', secure=True)
        message = _('Password: Invalid Length (must be 4 characters or more)')
        self._assert_response(response, status=400, message=message)

    @override_settings(ENFORCE_PASSWORD_POLICY=True, PASSWORD_MAX_LENGTH=12)
    def test_with_long_password(self):
        """
        Try (and fail) user creation with longer password
        """
        response = self._do_post_request(self.user_url, 'test', 'test_password', email='test@edx.org',
                                         first_name='John', last_name='Doe', secure=True)
        message = _('Password: Invalid Length (must be 12 characters or less)')
        self._assert_response(response, status=400, message=message)

    @override_settings(ENFORCE_PASSWORD_POLICY=True,
                       PASSWORD_COMPLEXITY={'UPPER': 2, 'LOWER': 2, 'PUNCTUATION': 2, 'DIGITS': 2})
    def test_password_without_uppercase(self):
        """
        Try (and fail) user creation since password should have atleast
        2 upper characters
        """
        response = self._do_post_request(self.user_url, 'test', 'test.pa64!', email='test@edx.org',
                                         first_name='John', last_name='Doe', secure=True)
        message = _('Password: Must be more complex (must contain 2 or more uppercase characters)')
        self._assert_response(response, status=400, message=message)

    @override_settings(ENFORCE_PASSWORD_POLICY=True,
                       PASSWORD_COMPLEXITY={'UPPER': 2, 'LOWER': 2, 'PUNCTUATION': 2, 'DIGITS': 2})
    def test_password_without_lowercase(self):
        """
        Try (and fail) user creation without any numeric characters
        in password
        """
        response = self._do_post_request(self.user_url, 'test', 'TEST.PA64!', email='test@edx.org',
                                         first_name='John', last_name='Doe', secure=True)
        message = _('Password: Must be more complex (must contain 2 or more lowercase characters)')
        self._assert_response(response, status=400, message=message)

    @override_settings(ENFORCE_PASSWORD_POLICY=True,
                       PASSWORD_COMPLEXITY={'UPPER': 2, 'LOWER': 2, 'PUNCTUATION': 2, 'DIGITS': 2})
    def test_password_without_punctuation(self):
        """
        Try (and fail) user creation without any punctuation in password
        """
        response = self._do_post_request(self.user_url, 'test', 'test64SS', email='test@edx.org',
                                         first_name='John', last_name='Doe', secure=True)
        message = _('Password: Must be more complex (must contain 2 or more uppercase characters,'
                    ' must contain 2 or more punctuation characters)')
        self._assert_response(response, status=400, message=message)

    @override_settings(ENFORCE_PASSWORD_POLICY=True,
                       PASSWORD_COMPLEXITY={'UPPER': 2, 'LOWER': 2, 'PUNCTUATION': 2, 'DIGITS': 2})
    def test_password_without_numeric(self):
        """
        Try (and fail) user creation without any numeric characters in password
        """
        response = self._do_post_request(self.user_url, 'test', 'test.paSS!', email='test@edx.org',
                                         first_name='John', last_name='Doe', secure=True)
        message = _('Password: Must be more complex (must contain 2 or more uppercase characters,'
                    ' must contain 2 or more digits)')
        self._assert_response(response, status=400, message=message)

    @override_settings(ENFORCE_PASSWORD_POLICY=True,
                       PASSWORD_COMPLEXITY={'UPPER': 2, 'LOWER': 2, 'PUNCTUATION': 2, 'DIGITS': 2})
    def test_password_with_complexity(self):
        """
        This should pass since it has everything needed for a complex password
        """
        response = self._do_post_request(self.user_url, str(uuid.uuid4()), 'Test.Me64!', email='test@edx.org',
                                         first_name='John', last_name='Doe', secure=True)
        self._assert_response(response, status=201)

    def test_user_with_invalid_email(self):
        """
        Try (and fail) user creation with invalid email address
        """
        response = self._do_post_request(self.user_url, 'test', 'Test.Me64!', email='test-edx.org',
                                         first_name='John', last_name='Doe', secure=True)
        message = _('Valid e-mail is required.')
        self._assert_response(response, status=400, message=message)

    def test_user_with_invalid_username(self):
        """
        Try (and fail) user creation with invalid username
        """
        response = self._do_post_request(self.user_url, 'user name', 'Test.Me64!', email='test@edx.org',
                                         first_name='John', last_name='Doe', secure=True)
        message = _('Username should only consist of A-Z and 0-9, with no spaces.')
        self._assert_response(response, status=400, message=message)

    def _do_post_request(self, url, username, password, **kwargs):
        """
        Post the login info
        """
        post_params, extra = {'username': username, 'password': password}, {}
        if kwargs.get('email'):
            post_params['email'] = kwargs.get('email')
        if kwargs.get('first_name'):
            post_params['first_name'] = kwargs.get('first_name')
        if kwargs.get('last_name'):
            post_params['last_name'] = kwargs.get('last_name')

        headers = {'X-Edx-Api-Key': TEST_API_KEY, 'Content-Type': 'application/json'}
        if kwargs.get('secure', False):
            extra['wsgi.url_scheme'] = 'https'
        return self.client.post(url, post_params, headers=headers, **extra)

    def _assert_response(self, response, status=200, success=None, message=None):
        """
        Assert that the response had status 200 and returned a valid
        JSON-parseable dict.

        If success is provided, assert that the response had that
        value for 'success' in the JSON dict.

        If message is provided, assert that the response contained that
        value for 'message' in the JSON dict.
        """
        self.assertEqual(response.status_code, status)

        try:
            response_dict = json.loads(response.content)
        except ValueError:
            self.fail("Could not parse response content as JSON: %s"
                      % str(response.content))

        if success is not None:
            self.assertEqual(response_dict['success'], success)

        if message is not None:
            msg = ("'%s' did not contain '%s'" %
                   (response_dict['message'], message))
            self.assertTrue(message in response_dict['message'], msg)
