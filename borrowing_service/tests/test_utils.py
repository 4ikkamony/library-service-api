from datetime import datetime, timedelta, date
from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch

from borrowing_service import utils
from borrowing_service.models import Borrowing
from django.contrib.auth import get_user_model
from book_service.models import Book  # or wherever your Book model is defined


User = get_user_model()


class TodayOverdueBorrowingsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            first_name='User',
            last_name="Test",
            email="user@test.com",
            password="testPasw14"
        )
        self.book = Book.objects.create(
            title="Test book",
            author="Test author",
            cover="soft",
            inventory=10,
            daily_fee=5.0,
        )

        self.start_time = datetime(2025, 1, 1, hour=12, minute=0)

        self.borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=self.start_time.date() + timedelta(days=5),
        )


    @patch("borrowing_service.utils.timezone")
    def test_today_overdue_borrowings(self, mock_timezone):
        fake_now = self.start_time + timedelta(days=10)
        mock_timezone.now.return_value = fake_now

        today, overdue_borrowings = utils.today_overdue_borrowings()

        self.assertEqual(today, fake_now.date())

        self.assertIn(self.borrowing, overdue_borrowings)
        self.assertEqual(overdue_borrowings.count(), 1)
