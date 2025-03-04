from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from unittest.mock import patch
from datetime import timedelta
import time
import stripe

from payment_service.models import Payment
from borrowing_service.models import Borrowing
from book_service.models import Book


class PaymentViewsTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email="paymentuser@example.com", password="password123"
        )
        self.staff_user = self.User.objects.create_user(
            email="staffuser@example.com", password="password321", is_staff=True
        )

        self.book = Book.objects.create(
            title="Test Book",
            author="Author Name",
            cover="hard",
            inventory=10,
            daily_fee=5.00,
        )

        self.borrowing = Borrowing.objects.create(
            expected_return_date=timezone.now().date() + timedelta(days=7),
            book=self.book,
            user=self.user,
        )

        self.payment = Payment.objects.create(
            borrowing=self.borrowing,
            money_to_pay=10.00,
            status=Payment.Status.PENDING,
            type=Payment.Type.PAYMENT,
            session_id="test_session_123",
        )

    def test_list_payments_regular_user(self):
        self.client.force_authenticate(user=self.user)
        url = "/api/payments/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        if not response.data.get("results"):
            self.fail("No data found in 'results' field of response")

        payments = response.data["results"]
        self.assertGreater(len(payments), 0, "Payments list is empty")
        payment_ids = {item["id"] for item in payments}
        self.assertEqual(len(payment_ids), 1)
        self.assertEqual(payment_ids.pop(), self.payment.id)

    def test_detail_payment_regular_user(self):
        self.client.force_authenticate(user=self.user)
        url = f"/api/payments/{self.payment.id}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_detail_payment_forbidden(self):
        other_user = self.User.objects.create_user(
            email="other@example.com", password="password"
        )
        borrowing2 = Borrowing.objects.create(
            expected_return_date=timezone.now().date() + timedelta(days=7),
            book=self.book,
            user=other_user,
        )
        payment2 = Payment.objects.create(
            borrowing=borrowing2,
            money_to_pay=20.00,
            status=Payment.Status.PENDING,
            type=Payment.Type.PAYMENT,
            session_id="other_session_456",
        )
        self.client.force_authenticate(user=self.user)
        url = f"/api/payments/{payment2.id}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("payment_service.views.notify_successful_payment")
    @patch("stripe.checkout.Session.retrieve")
    def test_success_payment_paid(self, mock_stripe_retrieve, mock_notify):
        stripe_response = type("obj", (object,), {"payment_status": "paid"})
        mock_stripe_retrieve.return_value = stripe_response

        self.client.force_authenticate(user=self.user)
        url = (
            reverse("payment_service:payment-success")
            + f"?session_id={self.payment.session_id}"
        )
        response = self.client.post(url, data={})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.Status.PAID)
        mock_notify.assert_called_once_with(self.payment.id)

    def test_success_payment_missing_session_id(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("payment_service:payment-success")
        response = self.client.post(url, data={})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Session ID is required", response.data.get("error", ""))

    @patch("stripe.checkout.Session.retrieve")
    def test_success_payment_not_paid(self, mock_stripe_retrieve):
        stripe_response = type("obj", (object,), {"payment_status": "unpaid"})
        mock_stripe_retrieve.return_value = stripe_response

        self.client.force_authenticate(user=self.user)
        url = (
            reverse("payment_service:payment-success")
            + f"?session_id={self.payment.session_id}"
        )
        response = self.client.post(url, data={})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Payment not completed", response.data.get("message", ""))

    def test_cancel_payment(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("payment_service:payment-cancel")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data.get("message"), "Payment was canceled. No charges were made."
        )

    @patch("payment_service.views.create_stripe_session")
    def test_renew_stripe_session_success(self, mock_create_session):
        self.payment.status = Payment.Status.EXPIRED
        self.payment.save()

        fake_session = {
            "url": "http://fake.stripe.session.url",
            "id": "new_session_id_789",
            "expires_at": int(time.time()) + 3600,
        }
        mock_create_session.return_value = fake_session

        self.client.force_authenticate(user=self.user)
        url = reverse("payment_service:renew")
        data = {"payment_id": self.payment.id}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.session_url, fake_session["url"])
        self.assertEqual(self.payment.session_id, fake_session["id"])
        self.assertEqual(self.payment.status, Payment.Status.PENDING)
        self.assertIn("Payment session renewed", response.data.get("message", ""))

    def test_renew_stripe_session_not_expired(self):
        self.payment.status = Payment.Status.PAID
        self.payment.save()
        self.client.force_authenticate(user=self.user)
        url = reverse("payment_service:renew")
        data = {"payment_id": self.payment.id}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Payment is not expired", response.data.get("error", ""))

    def test_renew_stripe_session_permission_denied(self):
        other_user = self.User.objects.create_user(
            email="other@example.com", password="password"
        )
        borrowing2 = Borrowing.objects.create(
            expected_return_date=timezone.now().date() + timedelta(days=7),
            book=self.book,
            user=other_user,
        )
        payment2 = Payment.objects.create(
            borrowing=borrowing2,
            money_to_pay=15.00,
            status=Payment.Status.EXPIRED,
            type=Payment.Type.PAYMENT,
            session_id="session_other",
        )
        self.client.force_authenticate(user=self.user)
        url = reverse("payment_service:renew")
        data = {"payment_id": payment2.id}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_renew_stripe_session_missing_payment_id(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("payment_service:renew")
        data = {}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("payment_id is required", response.data.get("error", ""))
