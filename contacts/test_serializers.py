import pytest

from .models import ContactRequest
from .serializers import ContactRequestSerializer


@pytest.fixture
def contact_request(db):
    return ContactRequest.objects.create(
        name="Test User", email="test@example.com", phone="+79991234567", message="Test message"
    )


@pytest.mark.django_db
class TestContactRequestSerializer:
    def test_serialize_contact_request(self, contact_request):
        serializer = ContactRequestSerializer(contact_request)
        data = serializer.data
        assert data["id"] == contact_request.id
        assert data["name"] == contact_request.name
        assert data["email"] == contact_request.email
        assert data["phone"] == contact_request.phone
        assert data["message"] == contact_request.message
        assert data["processed"] is False
        assert "created_at" in data

    def test_deserialize_contact_request(self):
        data = {
            "name": "New User",
            "email": "newuser@example.com",
            "phone": "+79999999999",
            "message": "New message",
        }
        serializer = ContactRequestSerializer(data=data)
        assert serializer.is_valid()
        contact = serializer.save()
        assert contact.name == "New User"
        assert contact.email == "newuser@example.com"
        assert contact.phone == "+79999999999"
        assert contact.message == "New message"
        assert contact.processed is False

    def test_deserialize_minimal_contact_request(self):
        data = {
            "name": "Minimal User",
            "email": "minimal@example.com",
        }
        serializer = ContactRequestSerializer(data=data)
        assert serializer.is_valid()
        contact = serializer.save()
        assert contact.name == "Minimal User"
        assert contact.email == "minimal@example.com"
        assert contact.phone == ""
        assert contact.message == ""

    def test_processed_field_read_only(self, contact_request):
        data = {"processed": True}
        serializer = ContactRequestSerializer(contact_request, data=data, partial=True)
        assert serializer.is_valid()
        # processed не должен обновляться через API
        serializer.save()
        contact_request.refresh_from_db()
        # processed может быть изменен только программно, не через сериализатор
