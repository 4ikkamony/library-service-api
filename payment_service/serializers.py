from rest_framework import serializers

from payment_service.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = (
            "id",
            "borrowing",
            "session_url",
            "session_id",
            "money_to_pay",
            "status",
            "type"
        )


class PaymentListSerializer(PaymentSerializer):
    class Meta:
        model = Payment
        fields = (
            "id",
            "borrowing",
            "status"
        )
