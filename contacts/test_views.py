from unittest.mock import MagicMock, patch

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from .models import ContactRequest


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def contacts(db):
    return [
        ContactRequest.objects.create(
            name=f"User {i}", email=f"user{i}@example.com", phone=f"+7999123456{i}"
        )
        for i in range(5)
    ]


@pytest.mark.django_db
class TestContactRequestViewSet:
    def test_list_pagination(self, api_client, contacts):
        response = api_client.get("/api/contacts/")
        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data
        assert "count" in response.data

    def test_empty_list(self, api_client):
        response = api_client.get("/api/contacts/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0

    @patch("contacts.views.pika.BlockingConnection")
    def test_create_contact_request_message_format(self, mock_connection, api_client):
        mock_channel = MagicMock()
        mock_conn = MagicMock()
        mock_conn.channel.return_value = mock_channel
        mock_connection.return_value = mock_conn

        contact_data = {
            "name": "Test User",
            "email": "test@example.com",
            "phone": "+79991234567",
            "message": "Test message",
        }
        response = api_client.post("/api/contacts/", contact_data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        # Проверяем формат сообщения в RabbitMQ
        call_args = mock_channel.basic_publish.call_args
        import json

        message_body = json.loads(call_args[1]["body"])
        assert message_body["name"] == contact_data["name"]
        assert message_body["email"] == contact_data["email"]
        assert message_body["phone"] == contact_data["phone"]
        assert message_body["message"] == contact_data["message"]
        assert "contact_request_id" in message_body

    def test_partial_update_contact_request(self, api_client, db):
        contact = ContactRequest.objects.create(name="Original Name", email="original@example.com")
        update_data = {"name": "Updated Name"}
        response = api_client.patch(f"/api/contacts/{contact.id}/", update_data, format="json")
        assert response.status_code == status.HTTP_200_OK
        contact.refresh_from_db()
        assert contact.name == "Updated Name"
        assert contact.email == "original@example.com"
