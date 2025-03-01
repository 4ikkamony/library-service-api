from rest_framework import serializers

from payment_service.models import Payment
from borrowing_service.serializers import BorrowingSerializer, BorrowingListSerializer


class PaymentSerializer(serializers.ModelSerializer):
    borrowing = BorrowingSerializer(many=False, read_only=True)

    class Meta:
        model = Payment
        fields = (
            "id",
            "borrowing",
            "status",
            "type",
            "money_to_pay",
            "session_url",
            "session_id",
        )


class PaymentListSerializer(serializers.ModelSerializer):
    borrowing = BorrowingListSerializer(many=False, read_only=True)

    class Meta:
        model = Payment
        fields = (
            "id",
            "status",
            "borrowing",
        )
