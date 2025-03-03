from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from book_service.models import Book
from borrowing_service.models import Borrowing

User = get_user_model()


class BorrowingModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )
        self.book = Book.objects.create(
            title="Test Book",
            author="Test Author",
            cover=Book.CoverType.HARD,
            inventory=5,
            daily_fee=1.00,
        )
        self.borrow_date = timezone.now().date()
        self.valid_return_date = self.borrow_date + timezone.timedelta(days=7)

    def test_borrowing_creation_decreases_book_inventory(self):
        initial_inventory = self.book.inventory

        Borrowing.objects.create(
            book=self.book, user=self.user, expected_return_date=self.valid_return_date
        )

        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, initial_inventory - 1)

    def test_existing_borrowing_does_not_change_inventory(self):
        borrowing = Borrowing.objects.create(
            book=self.book, user=self.user, expected_return_date=self.valid_return_date
        )
        initial_inventory = self.book.inventory

        borrowing.expected_return_date += timezone.timedelta(days=1)
        borrowing.save()

        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, initial_inventory)

    def test_clean_with_zero_inventory_raises_error(self):
        self.book.inventory = 0
        self.book.save()

        borrowing = Borrowing(
            book=self.book, user=self.user, expected_return_date=self.valid_return_date
        )

        with self.assertRaises(ValidationError):
            borrowing.clean()

    def test_clean_with_past_expected_return_raises_error(self):
        past_date = self.borrow_date - timezone.timedelta(days=1)
        borrowing = Borrowing(
            book=self.book, user=self.user, expected_return_date=past_date
        )

        with self.assertRaises(ValidationError):
            borrowing.clean()

    def test_clean_with_early_actual_return_raises_error(self):
        early_return = self.borrow_date - timezone.timedelta(days=1)
        borrowing = Borrowing(
            book=self.book,
            user=self.user,
            expected_return_date=self.valid_return_date,
            actual_return_date=early_return,
        )

        with self.assertRaises(ValidationError):
            borrowing.clean()

    def test_valid_actual_return_date_passes_clean(self):
        actual_return = self.borrow_date + timezone.timedelta(days=3)
        borrowing = Borrowing(
            book=self.book,
            user=self.user,
            expected_return_date=self.valid_return_date,
            actual_return_date=actual_return,
        )

        try:
            borrowing.clean()
        except ValidationError:
            self.fail("clean() raised ValidationError unexpectedly!")

    def test_invalid_borrowing_not_saved(self):
        past_date = self.borrow_date - timezone.timedelta(days=1)

        with self.assertRaises(ValidationError):
            Borrowing.objects.create(
                book=self.book, user=self.user, expected_return_date=past_date
            )

        self.assertEqual(Borrowing.objects.count(), 0)
        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, 5)

    def test_string_representation(self):
        borrowing = Borrowing(
            book=self.book,
            user=self.user,
            borrow_date=self.borrow_date,
            expected_return_date=self.valid_return_date,
        )

        expected_str = (
            f"Borrowing {self.book} by {self.user} on {self.borrow_date}. "
            f"Expected return date {self.valid_return_date}"
        )
        self.assertEqual(str(borrowing), expected_str)

    def test_model_field_properties(self):
        meta: Options = Borrowing._meta  # type: ignore

        actual_return_field = meta.get_field("actual_return_date")
        expected_return_field = meta.get_field("expected_return_date")

        self.assertTrue(actual_return_field.null)
        self.assertTrue(actual_return_field.blank)
        self.assertFalse(expected_return_field.null)
        self.assertFalse(expected_return_field.blank)
