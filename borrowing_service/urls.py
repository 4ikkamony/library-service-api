from django.urls import path, include
from rest_framework.routers import DefaultRouter

from borrowing_service.views import BorrowingViewSet

router = DefaultRouter()
router.register("", BorrowingViewSet, basename="borrowings")
urlpatterns = [
    path("", include(router.urls)),
]

app_name = "borrowing_service"
