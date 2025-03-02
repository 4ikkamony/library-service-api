from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from book_service.models import Book
from book_service.serializers import (
    BookSerializer,
    BookListSerializer,
    BookDetailSerializer,
)

User = get_user_model()


class BookModelTest(TestCase):
    def test_create_book_with_positive_daily_fee(self):
        book = Book(
            title="Test Book",
            author="Test Author",
            cover=Book.CoverType.HARD,
            inventory=5,
            daily_fee=Decimal("10.50"),
        )
        book.full_clean()
        book.save()
        self.assertEqual(Book.objects.count(), 1)

    def test_create_book_with_invalid_daily_fee(self):
        book = Book(
            title="Invalid Book",
            author="Invalid Author",
            cover=Book.CoverType.SOFT,
            inventory=3,
            daily_fee=Decimal("-5.00"),
        )
        with self.assertRaises(ValidationError):
            book.full_clean()

    def test_string_representation(self):
        book = Book.objects.create(
            title="Sample Book",
            author="John Doe",
            cover=Book.CoverType.HARD,
            inventory=1,
            daily_fee=Decimal("5.00"),
        )
        self.assertEqual(str(book), "Sample Book by John Doe")


class SerializersTest(TestCase):
    def setUp(self):
        self.book_data = {
            "title": "Test Book",
            "author": "Test Author",
            "cover": "hard",
            "inventory": 10,
            "daily_fee": "15.99",
        }

    def test_book_serializer_fields(self):
        serializer = BookSerializer()
        fields = set(serializer.fields.keys())
        expected_fields = {"id", "title", "author", "inventory", "daily_fee"}
        self.assertEqual(fields, expected_fields)

    def test_book_list_serializer_fields(self):
        serializer = BookListSerializer()
        fields = set(serializer.fields.keys())
        expected_fields = {"id", "title", "author"}
        self.assertEqual(fields, expected_fields)

    def test_book_detail_serializer_fields(self):
        serializer = BookDetailSerializer()
        fields = set(serializer.fields.keys())
        expected_fields = {"id", "title", "author", "cover", "inventory", "daily_fee"}
        self.assertEqual(fields, expected_fields)

    def test_daily_fee_validation(self):
        invalid_data = self.book_data.copy()
        invalid_data["daily_fee"] = "0.00"
        serializer = BookDetailSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("daily_fee", serializer.errors)


class BookViewSetTest(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            email="admin@example.com", password="adminpass"
        )
        self.user = User.objects.create_user(
            email="user@example.com", password="userpass"
        )
        self.book = Book.objects.create(
            title="Existing Book",
            author="Existing Author",
            cover=Book.CoverType.HARD,
            inventory=5,
            daily_fee=Decimal("10.00"),
        )
        self.valid_payload = {
            "title": "New Book",
            "author": "New Author",
            "cover": "soft",
            "inventory": 7,
            "daily_fee": "12.50",
        }
        self.client = APIClient()

    def get_url(self, pk=None):
        if pk:
            return reverse("book_service:book_service-detail", args=[pk])
        return reverse("book_service:book_service-list")

    def test_list_books_unauthenticated(self):
        response = self.client.get(self.get_url(), {"ordering": "id"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_retrieve_book_unauthenticated(self):
        response = self.client.get(self.get_url(self.book.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Existing Book")

    def test_create_book_as_admin(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(self.get_url(), data=self.valid_payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Book.objects.count(), 2)

    def test_create_book_as_regular_user(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.get_url(), data=self.valid_payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_book_as_admin(self):
        self.client.force_authenticate(user=self.admin)
        data = {"title": "Updated Title"}
        response = self.client.patch(self.get_url(self.book.pk), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.book.refresh_from_db()
        self.assertEqual(self.book.title, "Updated Title")

    def test_delete_book_as_admin(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(self.get_url(self.book.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Book.objects.filter(pk=self.book.pk).exists())
        self.assertEqual(Book.objects.count(), 0)

    def test_serializer_class_selection(self):

        response = self.client.get(self.get_url())
        self.assertNotIn("cover", response.data["results"][0])

        response = self.client.get(self.get_url(self.book.pk))
        self.assertIn("cover", response.data)
