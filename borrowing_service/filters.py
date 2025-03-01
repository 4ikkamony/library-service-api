from django_filters import rest_framework as filters
from borrowing_service.models import Borrowing


class BorrowingFilter(filters.FilterSet):
    is_active = filters.BooleanFilter(method="filter_is_active")
    user_id = filters.NumberFilter(field_name="user__id")

    class Meta:
        model = Borrowing
        fields = ("is_active", "user_id")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.request if hasattr(self, "request") else None
        if request and not request.user.is_staff:
            self.filters.pop("user_id", None)

    def filter_is_active(self, queryset, name, value):
        return queryset.filter(actual_return_date__isnull=value)
