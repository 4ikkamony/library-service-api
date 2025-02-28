from unittest import TestCase

from django.contrib.auth import get_user_model
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

    def test_create_user_without_username(self):
        user_data = {
            "first_name": "Test",
            "last_name": "User",
            "email": "unique@test.com",
            "password": "testpassword",
        }

        response = self.client.post(REGISTER_URL, user_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("username", response.data)
        self.assertIn("email", response.data)
        self.assertEqual(user_data["email"], response.data["email"])

    def test_create_users_with_duplicate_email(self):
        user_data = {
            "first_name": "testfirst",
            "last_name": "testlast",
            "email": "test_1@test.com",
            "password": "testpassword",
        }
        response1 = self.client.post(REGISTER_URL, user_data)

        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        user_data_2 = {
            "first_name": "testfirstduplicate",
            "last_name": "testlastduplicate",
            "email": "test_1@test.com",
            "password": "testpassword",
        }
        response2 = self.client.post(REGISTER_URL, user_data_2)

        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response2.data["email"][0],
            "user with this email address already exists.",
        )

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

    def tearDown(self):
        get_user_model().objects.all().delete()
