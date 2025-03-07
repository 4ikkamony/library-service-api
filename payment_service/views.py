import stripe
from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.urls import reverse
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from payment_service.models import Payment
from payment_service.schemas import (
    list_payment_schema,
    success_payment_schema,
    cansel_payment_schema,
    renew_stripe_session_schema,
    detail_payment_schema,
)
from payment_service.serializers import PaymentSerializer, PaymentListSerializer
from payment_service.utils import create_stripe_session, datetime_from_timestamp
from payment_service.tasks import notify_successful_payment


stripe.api_key = settings.STRIPE_SECRET_KEY


@list_payment_schema
class ListPaymentView(generics.ListAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentListSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = self.queryset
        if self.request.user.is_staff:
            return queryset
        else:
            return queryset.filter(borrowing__user=self.request.user.id)


@detail_payment_schema
class DetailPaymentView(generics.RetrieveAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = self.queryset
        if self.request.user.is_staff:
            return queryset
        else:
            return queryset.filter(borrowing__user=self.request.user.id)


@success_payment_schema
class SuccessPaymentView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        session_id = request.query_params.get("session_id")

        if not session_id:
            return Response(
                {"error": "Session ID is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            payment = get_object_or_404(Payment, session_id=session_id)

            if (
                payment.borrowing.user.id != request.user.id
                and not request.user.is_superuser
            ):
                return Response(
                    {"error": "You don't have permission to view this payment"},
                    status=status.HTTP_403_FORBIDDEN,
                )

            checkout_session = stripe.checkout.Session.retrieve(session_id)

            if checkout_session.payment_status == "paid":
                with transaction.atomic():
                    payment.status = Payment.Status.PAID
                    payment.save()

                    if payment.type == Payment.Type.PAYMENT:
                        payment.borrowing.is_active = True
                        payment.borrowing.save()
                    elif payment.type == Payment.Type.FINE:
                        payment.borrowing.is_active = False
                        payment.borrowing.save()

                notify_successful_payment(payment.id)

                return Response(
                    {
                        "message": "Payment successful",
                        "payment": PaymentSerializer(payment).data,
                    }
                )
            else:
                return Response(
                    {
                        "message": "Payment not completed",
                        "status": checkout_session.payment_status,
                    }
                )

        except stripe.error.StripeError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CancelPaymentView(APIView):
    permission_classes = (IsAuthenticated,)

    @cansel_payment_schema
    def get(self, request, *args, **kwargs):
        return Response({"message": "Payment was canceled. No charges were made."})


class RenewStripeSessionView(APIView):
    permission_classes = (IsAuthenticated,)

    @renew_stripe_session_schema
    def post(self, request):
        payment_id = request.data.get("payment_id")

        if not payment_id:
            return Response(
                {
                    "error": "payment_id is required",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        payment = get_object_or_404(Payment, id=payment_id)
        if payment.status != payment.Status.EXPIRED:
            return Response(
                {
                    "error": "Payment is not expired",
                    "status": status.HTTP_400_BAD_REQUEST,
                }
            )

        if payment.borrowing.user.id != request.user.id and not request.user.is_staff:
            return Response(
                {"error": "You don't have permission to view this payment"},
                status=status.HTTP_403_FORBIDDEN,
            )

        success_url = (
            request.build_absolute_uri(reverse("payment_service:payment-success"))
        ) + "?session_id={CHECKOUT_SESSION_ID}"
        cancel_url = request.build_absolute_uri(
            reverse("payment_service:payment-cancel")
        )

        try:
            new_session = create_stripe_session(
                f"{payment.type} #{payment.id}",
                payment.money_to_pay,
                success_url,
                cancel_url,
            )
        except stripe.error.StripeError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                payment.session_url = new_session.get("url")
                payment.session_id = new_session.get("id")

                expires_at_timestamp = new_session.get("expires_at")
                expires_at_datetime = datetime_from_timestamp(expires_at_timestamp)

                payment.session_expires_at = expires_at_datetime

                payment.status = Payment.Status.PENDING

                payment.save()
        except Exception:
            return Response(
                {"error": "Failed to update payment session."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response(
            {
                "message": "Payment session renewed",
                "session_url": payment.session_url,
            },
            status=status.HTTP_200_OK,
        )
