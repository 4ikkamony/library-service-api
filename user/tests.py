from unittest import TestCase

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient


REGISTER_URL = reverse("user:create")
TOKEN_URL = reverse("user:token_obtain_pair")
MANAGE_URL = reverse("user:manage")


class AccountsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_data = {
            "first_name": "Test",
            "last_name": "User",
            "email": "testemail@test.com",
            "password": "testpassword",
        }
        self.client.post(REGISTER_URL, self.user_data)

    def test_user_without_first_name(self):
        user_data = {
            "last_name": "test_last_name",
            "email": "testuser2@test.com",
            "password": "testpassword",
        }
        response = self.client.post(REGISTER_URL, user_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["first_name"][0], "This field is required."
        )

    def test_user_without_last_name(self):
        user_data = {
            "first_name": "test_first_name",
            "email": "testuser3@test.com",
            "password": "testpassword",
        }
        response = self.client.post(REGISTER_URL, user_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["last_name"][0], "This field is required."
        )

    def test_user_get_tokens(self):
        token_data = {
            "email": "testemail@test.com",
            "password": "testpassword",
        }
        response = self.client.post(TOKEN_URL, token_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_get_page_me(self):
        token_data = {
            "email": "testemail@test.com",
            "password": "testpassword",
        }
        response = self.client.post(TOKEN_URL, token_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response2 = self.client.get(
            MANAGE_URL, HTTP_AUTHORIZATION=f"Bearer {response.data['access']}"
        )

        self.assertEqual(response2.status_code, status.HTTP_200_OK)
