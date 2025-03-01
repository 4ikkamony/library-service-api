from rest_framework import serializers

from payment_service.models import Payment


class PaymentSerializer(serializers.Serializer):
    class Meta:
        model = Payment
        fields = (
            "id",
            "borrowing",
            "session_url",
            "session_id",
            "money_to_pay",
            "status",
            "type",
        )


class PaymentListSerializer(serializers.Serializer):
    class Meta:
        model = Payment
        fields = (
            "id",
            "status",
            "borrowing",
        )
