from django.urls import include, path

from rest_framework.routers import DefaultRouter

from book_service.views import BookViewSet


router = DefaultRouter()
router.register(r"book", BookViewSet, basename="book_service")

urlpatterns = [
    path("", include(router.urls)),
]

app_name = "book_service"
