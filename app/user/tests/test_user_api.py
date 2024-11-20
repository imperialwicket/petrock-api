"""
Tests for the user api
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')
GENERIC_USER_POST = {
    'name': 'Test User',
    'email': 'test@example.com',
    'password': 'pass12345'
}


def create_user(**params):
    """Create and return a new user"""
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """Test the public features of the user api"""

    def setUp(self):
        self.client = APIClient()

    def test_create_user_success(self):
        """Test creating a user is successful"""

        res = self.client.post(CREATE_USER_URL, GENERIC_USER_POST)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=GENERIC_USER_POST['email'])
        self.assertTrue(user.check_password(GENERIC_USER_POST['password']))
        self.assertNotIn('password', res.data)

    def test_user_with_email_exists_error(self):
        """Test error returned if email already in use"""

        create_user(**GENERIC_USER_POST)
        res = self.client.post(CREATE_USER_URL, GENERIC_USER_POST)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short_error(self):
        """Test an error is returned if password is less than 5 chars"""
        postdata = {
            'email': 'test@example.com',
            'password': 'pw',
            'name': 'Test User',
        }
        res = self.client.post(CREATE_USER_URL, postdata)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
            email=postdata['email']
        ).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """Test generates token for valid credentials"""

        create_user(**GENERIC_USER_POST)

        postdata = {
            'email': GENERIC_USER_POST['email'],
            'password': GENERIC_USER_POST['password'],
        }
        res = self.client.post(TOKEN_URL, postdata)

        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_bad_credentials(self):
        """Test returns error if credentials invalid"""
        create_user(**GENERIC_USER_POST)

        postdata = {
            'email': GENERIC_USER_POST['email'],
            'password': 'not-the-right-password',
        }
        res = self.client.post(TOKEN_URL, postdata)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_blank_password(self):
        """Test posting a blank password returns error"""
        postdata = {'email': GENERIC_USER_POST['email'], 'password': ''}
        res = self.client.post(TOKEN_URL, postdata)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized(self):
        """Test authentication is required for users"""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    """Test api requests that require authentication."""

    def setUp(self):
        self.user = create_user(**GENERIC_USER_POST)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        """Test retrieving profile for logged in user"""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            'name': self.user.name,
            'email': self.user.email,
        })

    def test_post_me_not_allowed(self):
        """Test POST is not allowed for /me"""
        res = self.client.post(ME_URL, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        """Test updating the user profile for logged in user"""
        patchdata = {'name': 'New Name', 'password': 'yet-another-password'}

        res = self.client.patch(ME_URL, patchdata)

        self.user.refresh_from_db()
        self.assertEqual(self.user.name, patchdata['name'])
        self.assertTrue(self.user.check_password(patchdata['password']))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
