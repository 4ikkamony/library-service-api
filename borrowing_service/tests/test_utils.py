from datetime import datetime, timedelta
from django.test import TestCase
from unittest.mock import patch
from django.contrib.auth import get_user_model

from borrowing_service.models import Borrowing
from book_service.models import Book
from borrowing_service import utils


User = get_user_model()


class TodayOverdueBorrowingsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.timezone_patcher = patch("django.utils.timezone.now")
        cls.mock_now = cls.timezone_patcher.start()

    @classmethod
    def tearDownClass(cls):
        cls.timezone_patcher.stop()
        super().tearDownClass()

    def setUp(self):
        self.fixed_now = datetime(2025, 2, 24, 12, 0)
        self.mock_now.return_value = self.fixed_now

        self.user = User.objects.create(
            first_name="Test",
            last_name="Testenko",
            email="test@test.com",
            password="testPass14",
        )
        self.book = Book.objects.create(
            title="Test Book",
            author="test Author",
            cover="soft",
            daily_fee=5.0,
            inventory=5,
        )

        self.borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=self.fixed_now.date() + timedelta(days=5),
            actual_return_date=None,
        )

    def test_overdue_borrowings(self):
        future_time = self.fixed_now + timedelta(days=10)
        self.mock_now.return_value = future_time

        today, overdue_borrowings = utils.today_overdue_borrowings()

        self.assertEqual(today, future_time.date())
        self.assertIn(self.borrowing, overdue_borrowings)
        self.assertEqual(overdue_borrowings.count(), 1)

    def test_no_overdue_borrowings(self):
        non_overdue_time = self.fixed_now + timedelta(days=2)
        self.mock_now.return_value = non_overdue_time

        today, overdue_borrowings = utils.today_overdue_borrowings()

        self.assertEqual(today, non_overdue_time.date())
        self.assertEqual(overdue_borrowings.count(), 0)
