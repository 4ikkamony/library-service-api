from django.urls import path

from payment_service.views import (
    ListPaymentView,
    DetailPaymentView,
    SuccessPaymentView,
    CancelPaymentView
)

urlpatterns = [
    path("", ListPaymentView.as_view()),
    path("<int:pk>/", DetailPaymentView.as_view()),
    path("success/", SuccessPaymentView.as_view(), name="payment-success"),
    path("cancel/", CancelPaymentView.as_view(), name="payment-cancel"),
]

app_name = "payment_service"
