from django.db import transaction
from django.utils import timezone

from rest_framework import mixins, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiExample,
)

from borrowing_service.models import Borrowing
from borrowing_service.serializers import (
    BorrowingListSerializer,
    BorrowingDetailSerializer,
    BorrowingCreateSerializer,
    BorrowingReturnSerializer,
)
from payment_service.models import Payment
from payment_service.utils import create_payment_session


@extend_schema_view(
    list=extend_schema(
        description=(
            "Retrieve a list of borrowing records. "
            "Supports filtering by active status using the "
            "'is_active' query parameter "
            "(use 'true' for ongoing borrowings and 'false' for returned ones). "
            "For staff users, an additional 'user_id' filter is available."
        ),
        parameters=[
            OpenApiParameter(
                name="is_active",
                location=OpenApiParameter.QUERY,
                description="Filter by active status",
                required=False,
                type=bool,
            ),
            OpenApiParameter(
                name="user_id",
                location=OpenApiParameter.QUERY,
                description="(Staff only) Filter borrowings by a specific user ID",
                required=False,
                type=int,
            ),
        ],
        responses=BorrowingListSerializer(many=True),
    ),
    retrieve=extend_schema(
        description="Retrieve detailed information for a specific borrowing record.",
        responses=BorrowingDetailSerializer,
    ),
    create=extend_schema(
        description=(
            "Create a new borrowing record. "
            "The record is automatically linked to the authenticated user."
        ),
        request=BorrowingCreateSerializer,
        responses=BorrowingDetailSerializer,
    ),
)
class BorrowingViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet,
):
    """
    API endpoint for managing borrowing records.

    **List:** Returns a list of borrowing records with optional filtering.
    **Retrieve:** Gets detailed info for a specific borrowing record.
    **Create:** Creates a new borrowing record.
    **Return Borrowing:** Custom action to mark a borrowed book as returned.
    """

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

    @extend_schema(
        description=(
            "Mark a borrowed book as returned. This action sets the actual return date "
            "to the current date and increments the book's inventory. If the book "
            "is returned late, a FINE payment session is created, "
            "and the response includes a payment ID and a Stripe session URL."
        ),
        responses={
            200: [
                OpenApiExample(
                    "On-Time Return",
                    value={"message": "Book returned successfully"},
                ),
                OpenApiExample(
                    "Late Return with Fine",
                    value={
                        "message": "The book was returned late, you must pay a fine.",
                        "payment_id": 123,
                        "session_url": "https://stripe.example.com/session/abc123",
                    },
                ),
            ],
            400: OpenApiExample(
                "Already Returned",
                value={"error": "This book is already returned."},
            ),
        },
        methods=["POST"],
    )
    @action(
        detail=True,
        methods=["POST"],
        url_path="return",
        serializer_class=BorrowingReturnSerializer,
    )
    def return_borrowing(self, request, pk=None):
        borrowing = self.get_object()

        if borrowing.actual_return_date:
            return Response(
                {"error": "This book is already returned."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            borrowing.actual_return_date = timezone.now().date()
            borrowing.book.inventory += 1

            if borrowing.actual_return_date > borrowing.expected_return_date:
                payment, session_url = create_payment_session(
                    borrowing, request, Payment.Type.FINE
                )
                response_data = {
                    "message": "The book was returned late, you must pay a fine.",
                    "payment_id": payment.id,
                    "session_url": session_url,
                }
                return Response(response_data, status=status.HTTP_200_OK)

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
