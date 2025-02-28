from rest_framework import serializers

from payment_service.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    # user = serializers.SerializerMethodField()
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

    # def get_user(self, obj):
    #     if obj.borrowing:
    #         return obj.borrowing.user
    #     return None


class PaymentListSerializer(PaymentSerializer):
    class Meta:
        model = Payment
        fields = (
            "id",
            "borrowing",
            "status"
        )