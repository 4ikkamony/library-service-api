import stripe
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from payment_service.models import Payment
from payment_service.serializers import PaymentSerializer, PaymentListSerializer


stripe.api_key = settings.STRIPE_SECRET_KEY


class ListPaymentView(generics.ListAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentListSerializer

    def get_queryset(self):
        queryset = self.queryset
        if self.request.user.is_superuser:
            return queryset
        else:
            return queryset.filter(borrowing__user=self.request.user.id)


class DetailPaymentView(generics.RetrieveAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

    def get_queryset(self):
        queryset = self.queryset
        if self.request.user.is_superuser:
            return queryset
        else:
            return queryset.filter(borrowing__user=self.request.user.id)


class SuccessPaymentView(APIView):
    def get(self, request, *args, **kwargs):
        """
        Check successful Stripe payment and update payment status
        """
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
                payment.status = Payment.Status.PAID
                payment.save()

                if payment.type == Payment.Type.PAYMENT:
                    payment.borrowing.is_active = True
                    payment.borrowing.save()
                elif payment.type == Payment.Type.FINE:
                    payment.borrowing.is_active = False
                    payment.borrowing.save()

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
    def get(self, request, *args, **kwargs):
        return Response({"message": "Payment was canceled. No charges were made."})
