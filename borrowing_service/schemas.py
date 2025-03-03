from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiExample,
)

from borrowing_service.serializers import (
    BorrowingListSerializer,
    BorrowingDetailSerializer,
    BorrowingCreateSerializer,
)


borrowing_viewset_schema = extend_schema_view(
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

borrowing_return_schema = extend_schema(
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
