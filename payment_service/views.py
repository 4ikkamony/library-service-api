from rest_framework import viewsets

from payment_service.models import Payment
from payment_service.serializers import PaymentSerializer, PaymentListSerializer


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()

    def get_queryset(self):
        queryset = self.queryset

        if self.request.user.is_superuser:
            return queryset
        else:
            return queryset.filter(borrowing__user=self.request.user.id)

    def get_serializer_class(self):
        if self.action == "list":
            return PaymentListSerializer
        return PaymentSerializer
