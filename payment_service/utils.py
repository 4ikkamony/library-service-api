import datetime
from decimal import Decimal

import stripe
from django.conf import settings
from django.db.models import QuerySet
from django.urls import reverse
from django.utils import timezone

from payment_service.models import Payment


def expired_sessions() -> tuple[datetime, QuerySet]:
    current_time = timezone.now()
    return (
        current_time,
        Payment.objects.filter(
            session_expires_at__lt=current_time, status=Payment.Status.PENDING
        ),
    )


def create_payment_session(borrowing, request, payment_type=Payment.Type.PAYMENT):
    """
    Creates a new Stripe Checkout Session for a borrowing and saves the
    associated payment record in the database.

    Args:
        borrowing: The Borrowing object to create a payment for
        payment_type: Type of payment (Payment.Type.PAYMENT or Payment.Type.FINE)
        request: The request object to generate success/cancel URLs

    Returns:
        tuple: (Payment object, Stripe session URL)
    """

    if payment_type == Payment.Type.PAYMENT:
        money_to_pay = Decimal(
            borrowing.book.daily_fee
            * (borrowing.expected_return_date - borrowing.borrow_date).days
        )
        payment_description = f"Book rental: {borrowing.book.title}"

    elif payment_type == Payment.Type.FINE:
        money_to_pay = Decimal(
            borrowing.book.daily_fee
            * (borrowing.actual_return_date - borrowing.expected_return_date).days
        )
        payment_description = f"Late return fine: {borrowing.book.title}"
    else:
        raise ValueError(f"Invalid payment type: {payment_type}")

    success_url = request.build_absolute_uri(
        reverse("payment_service:payment-success")
    ) + "?session_id={CHECKOUT_SESSION_ID}"
    cancel_url = request.build_absolute_uri(reverse("payment_service:payment-cancel"))

    try:
        checkout_session = create_stripe_session(
            payment_description, money_to_pay, success_url, cancel_url
        )
    except stripe.error.StripeError as e:
        raise e

    payment = Payment.objects.create(
        borrowing=borrowing,
        status=Payment.Status.PENDING,
        type=payment_type,
        money_to_pay=money_to_pay,
        session_id=checkout_session.id,
        session_expires_at=datetime_from_timestamp(checkout_session.expires_at),
        session_url=checkout_session.url,
    )

    return payment, checkout_session.url


def create_stripe_session(product_description, money_to_pay, success_url, cancel_url):
    stripe.api_key = settings.STRIPE_SECRET_KEY

    return stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": product_description,
                    },
                    "unit_amount": int(money_to_pay * 100),
                },
                "quantity": 1,
            },
        ],
        mode="payment",
        success_url=success_url,
        cancel_url=cancel_url,
    )


def datetime_from_timestamp(timestamp: int):
    return datetime.datetime.fromtimestamp(timestamp, datetime.timezone.utc)
