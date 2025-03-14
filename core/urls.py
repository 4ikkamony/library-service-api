from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularSwaggerView, SpectacularAPIView

urlpatterns = [
    path(
        "api/",
        include(
            [
                path("books/", include("book_service.urls", namespace="book_service")),
                path(
                    "borrowings/",
                    include("borrowing_service.urls", namespace="borrowing_service"),
                ),
                path("payments/", include("payment_service.urls", namespace="payment_service")),
                path("users/", include("user.urls", namespace="user")),
                path("schema/", SpectacularAPIView.as_view(), name="schema"),
                path(
                    "doc/swagger/",
                    SpectacularSwaggerView.as_view(url_name="schema"),
                    name="swagger-ui",
                ),
            ]
        )
    ),
    path("admin/", admin.site.urls),
    path("__debug__/", include("debug_toolbar.urls")),
]
