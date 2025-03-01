from rest_framework import serializers

from borrowing_service.models import Borrowing
from borrowing_service.serializers import BorrowingListSerializer
from payment_service.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    borrowing = serializers.PrimaryKeyRelatedField(queryset=Borrowing.objects.all())

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
        read_only_fields = (
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
