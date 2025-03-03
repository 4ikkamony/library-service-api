from rest_framework import serializers

from book_service.models import Book


class BaseBookSerializer(serializers.ModelSerializer):
    def validate_daily_fee(self, value):
        if value <= 0:
            raise serializers.ValidationError("Daily fee has to be greater than 0.")
        return value


class BookSerializer(BaseBookSerializer):
    class Meta:
        model = Book
        fields = ["id", "title", "author", "inventory", "daily_fee"]


class BookListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ("id", "title", "author", "inventory")


class BookDetailSerializer(BaseBookSerializer):
    class Meta:
        model = Book
        fields = ("id", "title", "author", "cover", "inventory", "daily_fee")
