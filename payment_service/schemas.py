from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
)

from payment_service.serializers import PaymentSerializer, PaymentListSerializer

list_payment_schema = extend_schema(
    responses={
        200: PaymentListSerializer(many=True),
        401: {
            "description": "Unauthorized client",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {"error": {"type": "string"}},
                    }
                }
            }
        },
    },
    description="List all payments (staff users see all, regular users see only their own).",
)

detail_payment_schema = extend_schema(
    responses={
        200: PaymentSerializer(many=False),
        401: {
            "description": "Unauthorized client",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {"error": {"type": "string"}},
                    }
                }
            }
        },
        403: {
            "description": "Permission denied",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {"error": {"type": "string"}},
                    },
                },
            },
        },
    }
)

success_payment_schema = extend_schema(
    description="Check successful Stripe payment and update payment status",
    parameters=[
        OpenApiParameter(
            name="session_id",
            description="Stripe Checkout Session ID",
            required=True,
            type=str,
        ),
    ],
    responses={
        200: {
            "description": "Payment successful",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "example": "Payment successful",
                            },
                        },
                    },
                },
            },
        },
        400: {
            "description": "Bad request (missing session_id or Stripe error)",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {"error": {"type": "string"}},
                    },
                },
            },
        },
        401: {
            "description": "Unauthorized client",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {"error": {"type": "string"}},
                    }
                }
            }
        },
        403: {
            "description": "Permission denied",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {"error": {"type": "string"}},
                    },
                },
            },
        },
        404: {
            "description": "Error: Not Found",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "detail": {
                                "type": "string",
                                "example": "No Payment matches the given query.",
                            }
                        },
                    },
                },
            },
        },
    },
)

cansel_payment_schema = extend_schema(
    description="Handles canceled Stripe payment sessions",
    responses={
        200: {
            "type": "object",
            "properties": {"message": {"type": "string"}},
            "example": {"message": "Payment was canceled. No charges were made."},
        },
        401: {
            "description": "Unauthorized client",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {"error": {"type": "string"}},
                    }
                }
            }
        },
    },
)

renew_stripe_session_schema = extend_schema(
    parameters=[
        OpenApiParameter(
            name="session_id",
            description="Stripe Checkout Session ID",
            required=True,
            type=str,
        ),
    ],
    responses={
        200: {
            "description": "Payment session renewed successfully",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "example": "Payment session renewed",
                            },
                            "session_url": {
                                "type": "string",
                                "example": "https://checkout.stripe.com/...",
                            },
                        },
                    },
                },
            },
        },
        400: {
            "description": "Bad request (missing payment_id, "
                           "payment not expired, Stripe error)",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {"error": {"type": "string"}},
                    },
                },
            },
        },
        401: {
            "description": "Unauthorized client",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {"error": {"type": "string"}},
                    }
                }
            }
        },
        403: {
            "description": "Permission denied",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {"error": {"type": "string"}},
                    },
                },
            },
        },
        404: {
            "description": "Error: Not Found",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "detail": {
                                "type": "string",
                                "example": "No Payment matches the given query.",
                            }
                        },
                    },
                },
            },
        },
        500: {
            "description": "Internal server error (failed to update payment session)",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {"error": {"type": "string"}},
                    },
                },
            },
        },
    },
    description="Renews an expired Stripe payment session.",
)
