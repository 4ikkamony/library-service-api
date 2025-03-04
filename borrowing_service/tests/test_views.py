from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from borrowing_service.models import Borrowing
from book_service.models import Book

User = get_user_model()


class BorrowingViewSetTest(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.timezone_patcher = patch("borrowing_service.models.timezone.now")
        cls.mock_now = cls.timezone_patcher.start()
        cls.payment_patcher = patch(
            "borrowing_service.views.create_payment_session",
            return_value=(MagicMock(id=1), "mocked_url"),
        )
        cls.mock_payment = cls.payment_patcher.start()
        cls.stripe_patcher = patch("stripe.api_key", "sk_test_mock_key")
        cls.stripe_patcher.start()
        # Mock Celery task
        cls.celery_patcher = patch("borrowing_service.views.notify_new_borrowing.delay")
        cls.mock_celery = cls.celery_patcher.start()

    @classmethod
    def tearDownClass(cls):
        cls.timezone_patcher.stop()
        cls.payment_patcher.stop()
        cls.stripe_patcher.stop()
        cls.celery_patcher.stop()
        super().tearDownClass()

    def setUp(self):
        Borrowing.objects.all().delete()
        self.fixed_now = datetime(2025, 3, 2, 12, 0)
        self.mock_now.return_value = self.fixed_now
        self.user = User.objects.create_user(
            email="testuser@example.com", password="testpass"
        )
        self.admin = User.objects.create_superuser(
            email="admin@example.com", password="adminpass"
        )
        self.client.force_authenticate(user=self.user)
        self.book = Book.objects.create(title="Test Book", inventory=5, daily_fee=10)

    def test_create_borrowing(self):
        data = {"book": self.book.id, "expected_return_date": "2025-03-10"}
        response = self.client.post("/api/borrowings/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertIn("id", response.data)
        self.assertIn("expected_return_date", response.data)
        self.assertIn("book", response.data)
        self.assertIn("payment_id", response.data)
        self.assertIn("session_url", response.data)

        self.assertEqual(response.data["expected_return_date"], "2025-03-10")
        self.assertEqual(response.data["book"], self.book.id)
        self.assertEqual(response.data["payment_id"], 1)
        self.assertEqual(response.data["session_url"], "mocked_url")

    def test_user_sees_only_own_borrowings(self):
        Borrowing.objects.create(
            user=self.user, book=self.book, expected_return_date=timezone.now().date()
        )
        other_user = User.objects.create_user(
            email="otheruser@example.com", password="otherpass"
        )
        Borrowing.objects.create(
            user=other_user, book=self.book, expected_return_date=timezone.now().date()
        )
        response = self.client.get("/api/borrowings/")
        self.assertEqual(len(response.data), 4)

    def test_admin_sees_all_borrowings(self):
        self.client.force_authenticate(user=self.admin)
        Borrowing.objects.create(
            user=self.user, book=self.book, expected_return_date=timezone.now().date()
        )
        other_user = User.objects.create_user(
            email="otheruser@example.com", password="otherpass"
        )
        Borrowing.objects.create(
            user=other_user, book=self.book, expected_return_date=timezone.now().date()
        )
        response = self.client.get("/api/borrowings/")
        self.assertEqual(len(response.data), 4)

    def test_filter_active_borrowings(self):
        Borrowing.objects.create(
            user=self.user, book=self.book, expected_return_date=timezone.now().date()
        )
        Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=timezone.now().date(),
            actual_return_date=timezone.now().date(),
        )
        response = self.client.get("/api/borrowings/?is_active=true")
        self.assertEqual(len(response.data), 4)

    def test_admin_filter_by_user_id(self):
        self.client.force_authenticate(user=self.admin)
        other_user = User.objects.create_user(
            email="otheruser@example.com", password="otherpass"
        )
        Borrowing.objects.create(
            user=self.user, book=self.book, expected_return_date=timezone.now().date()
        )
        Borrowing.objects.create(
            user=other_user, book=self.book, expected_return_date=timezone.now().date()
        )
        response = self.client.get(f"/api/borrowings/?user_id={self.user.id}")
        self.assertEqual(len(response.data), 4)
