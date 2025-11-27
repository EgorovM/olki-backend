from rest_framework import serializers

from .models import ContactRequest


class ContactRequestSerializer(serializers.ModelSerializer):
    """Сериализатор для запроса на контакт"""

    class Meta:
        model = ContactRequest
        fields = ["id", "name", "email", "phone", "message", "created_at", "processed"]
        read_only_fields = ["created_at", "processed"]
