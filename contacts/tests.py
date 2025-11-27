from unittest.mock import MagicMock, patch

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from .models import ContactRequest


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def contact_data():
    return {
        "name": "Иван Иванов",
        "email": "ivan@example.com",
        "phone": "+79991234567",
        "message": "Хочу узнать больше о красках",
    }


@pytest.fixture
def contact_request(db, contact_data):
    return ContactRequest.objects.create(**contact_data)


@pytest.mark.django_db
class TestContactRequestModel:
    def test_create_contact_request(self, contact_data):
        contact = ContactRequest.objects.create(**contact_data)
        assert contact.name == contact_data["name"]
        assert contact.email == contact_data["email"]
        assert contact.phone == contact_data["phone"]
        assert contact.message == contact_data["message"]
        assert contact.processed is False
        assert contact.id is not None

    def test_contact_request_str(self, contact_request):
        expected = f"{contact_request.name} ({contact_request.email})"
        assert str(contact_request) == expected

    def test_contact_request_ordering(self, db):
        contact1 = ContactRequest.objects.create(name="Name 1", email="email1@test.com")
        contact2 = ContactRequest.objects.create(name="Name 2", email="email2@test.com")
        contacts = list(ContactRequest.objects.all())
        assert contacts[0] == contact2
        assert contacts[1] == contact1

    def test_contact_request_optional_fields(self, db):
        contact = ContactRequest.objects.create(name="Test", email="test@example.com")
        assert contact.phone == ""
        assert contact.message == ""
        assert contact.processed is False


@pytest.mark.django_db
class TestContactRequestAPI:
    def test_list_contact_requests(self, api_client, contact_request):
        response = api_client.get("/api/contacts/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["name"] == contact_request.name

    def test_retrieve_contact_request(self, api_client, contact_request):
        response = api_client.get(f"/api/contacts/{contact_request.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == contact_request.name
        assert response.data["email"] == contact_request.email

    @patch("contacts.views.pika.BlockingConnection")
    def test_create_contact_request_sends_to_rabbitmq(
        self, mock_connection, api_client, contact_data
    ):
        mock_channel = MagicMock()
        mock_conn = MagicMock()
        mock_conn.channel.return_value = mock_channel
        mock_connection.return_value = mock_conn

        response = api_client.post("/api/contacts/", contact_data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert "message" in response.data
        assert ContactRequest.objects.count() == 1

        # Проверяем, что сообщение было отправлено в RabbitMQ
        mock_channel.queue_declare.assert_called_once()
        mock_channel.basic_publish.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("contacts.views.pika.BlockingConnection")
    def test_create_contact_request_handles_rabbitmq_error(
        self, mock_connection, api_client, contact_data
    ):
        mock_connection.side_effect = Exception("Connection error")

        response = api_client.post("/api/contacts/", contact_data, format="json")

        # Запрос все равно должен быть создан, даже если RabbitMQ недоступен
        assert response.status_code == status.HTTP_201_CREATED
        assert ContactRequest.objects.count() == 1

    def test_create_contact_request_minimal_data(self, api_client):
        minimal_data = {
            "name": "Test User",
            "email": "test@example.com",
        }
        response = api_client.post("/api/contacts/", minimal_data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        contact = ContactRequest.objects.first()
        assert contact.phone == ""
        assert contact.message == ""

    def test_update_contact_request(self, api_client, contact_request):
        update_data = {
            "name": "Updated Name",
            "email": "updated@example.com",
            "phone": "+79999999999",
            "message": "Updated message",
        }
        response = api_client.put(
            f"/api/contacts/{contact_request.id}/", update_data, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        contact_request.refresh_from_db()
        assert contact_request.name == "Updated Name"

    def test_delete_contact_request(self, api_client, contact_request):
        response = api_client.delete(f"/api/contacts/{contact_request.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert ContactRequest.objects.count() == 0


@pytest.mark.django_db
class TestWorker:
    @patch("contacts.management.commands.runworker.send_mail")
    def test_process_message_sends_emails(self, mock_send_mail, contact_request):
        from contacts.management.commands.runworker import Command

        command = Command()
        message = {
            "contact_request_id": contact_request.id,
            "name": contact_request.name,
            "email": contact_request.email,
            "phone": contact_request.phone,
            "message": contact_request.message,
        }

        command.process_message(message)

        # Проверяем, что отправлено 2 письма (пользователю и сервису)
        assert mock_send_mail.call_count == 2

        # Проверяем письмо пользователю
        user_call = mock_send_mail.call_args_list[0]
        assert "Спасибо" in user_call[0][0]  # subject
        assert contact_request.email in user_call[0][3]  # recipient_list

        # Проверяем письмо сервису
        service_call = mock_send_mail.call_args_list[1]
        assert "Новый запрос" in service_call[0][0]  # subject

        # Проверяем, что запрос помечен как обработанный
        contact_request.refresh_from_db()
        assert contact_request.processed is True

    @patch("contacts.management.commands.runworker.send_mail")
    def test_process_message_handles_missing_contact(self, mock_send_mail):
        from contacts.management.commands.runworker import Command

        command = Command()
        message = {
            "contact_request_id": 99999,
            "name": "Test",
            "email": "test@example.com",
            "phone": "",
            "message": "",
        }

        # Не должно быть исключения
        command.process_message(message)

        # Письма все равно должны быть отправлены
        assert mock_send_mail.call_count == 2

    @patch("contacts.management.commands.runworker.send_mail")
    def test_send_thank_you_email(self, mock_send_mail):
        from django.conf import settings

        from contacts.management.commands.runworker import Command

        command = Command()
        command.send_thank_you_email("Иван", "ivan@example.com")

        mock_send_mail.assert_called_once()
        call_args = mock_send_mail.call_args
        assert "Спасибо" in call_args[0][0]  # subject
        assert "Иван" in call_args[0][1]  # message
        assert call_args[0][2] == settings.DEFAULT_FROM_EMAIL
        assert call_args[0][3] == ["ivan@example.com"]

    @patch("contacts.management.commands.runworker.send_mail")
    def test_send_service_notification(self, mock_send_mail):
        from django.conf import settings

        from contacts.management.commands.runworker import Command

        command = Command()
        command.send_service_notification(
            "Иван", "ivan@example.com", "+79991234567", "Test message"
        )

        mock_send_mail.assert_called_once()
        call_args = mock_send_mail.call_args
        assert "Новый запрос" in call_args[0][0]  # subject
        assert "Иван" in call_args[0][1]  # message
        assert call_args[0][2] == settings.DEFAULT_FROM_EMAIL
        assert call_args[0][3] == [settings.SERVICE_EMAIL]
