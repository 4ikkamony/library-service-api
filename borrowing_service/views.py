from django.utils import timezone
from rest_framework import mixins, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from borrowing_service.models import Borrowing
from borrowing_service.serializers import (
    BorrowingListSerializer,
    BorrowingDetailSerializer,
    BorrowingCreateSerializer,
    BorrowingReturnSerializer,
)


class BorrowingViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet,
):
    queryset = Borrowing.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            if is_active.lower() in ["true", "1", "yes"]:
                qs = qs.filter(actual_return_date__isnull=True)
            elif is_active.lower() in ["false", "0", "no"]:
                qs = qs.filter(actual_return_date__isnull=False)

        if not user.is_staff:
            qs = qs.filter(user=user)
        else:
            user_id = self.request.query_params.get("user_id")
            if user_id:
                qs = qs.filter(user__id=user_id)
        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return BorrowingListSerializer

        if self.action == "retrieve":
            return BorrowingDetailSerializer

        if self.action == "return_borrowing":
            return BorrowingReturnSerializer

        return BorrowingCreateSerializer

    @action(
        detail=True,
        methods=["POST"],
        url_path="return",
        serializer_class=BorrowingReturnSerializer,
    )
    def return_borrowing(self, request, pk=None):
        borrowing = self.get_object()

        if borrowing.actual_return_date:
            return Response({"error": "This book is already returned."})

        borrowing.actual_return_date = timezone.now().date()
        borrowing.book.inventory += 1
        borrowing.book.save()
        borrowing.save()
        return Response(
            {"message": "Book returned successfully"}, status=status.HTTP_200_OK
        )

    def perform_create(self, serializer):
        user = self.request.user

        if not user.is_authenticated:
            raise ValidationError("User must be authenticated")

        serializer.save(user=user)
