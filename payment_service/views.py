from urllib import request

from django.shortcuts import render
from rest_framework import viewsets

from payment_service.models import Payment
from payment_service.serializers import PaymentSerializer, PaymentListSerializer


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return PaymentListSerializer
        return PaymentSerializer
