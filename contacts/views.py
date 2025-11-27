import json

import pika
from django.conf import settings
from rest_framework import status, viewsets
from rest_framework.response import Response

from .models import ContactRequest
from .serializers import ContactRequestSerializer


class ContactRequestViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с запросами на контакт"""

    queryset = ContactRequest.objects.all()
    serializer_class = ContactRequestSerializer

    def create(self, request, *args, **kwargs):
        """Создать запрос на контакт и отправить событие в RabbitMQ"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        contact_request = serializer.save()

        # Отправляем событие в RabbitMQ для обработки воркером
        try:
            self._send_to_rabbitmq(contact_request)
        except Exception as e:
            # Логируем ошибку, но не прерываем создание запроса
            print(f"Error sending to RabbitMQ: {e}")

        # Возвращаем успешный ответ сразу
        headers = self.get_success_headers(serializer.data)
        return Response(
            {
                "message": "Спасибо за ваш запрос! Мы свяжемся с вами в ближайшее время.",
                "data": serializer.data,
            },
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

    def _send_to_rabbitmq(self, contact_request):
        """Отправить событие в RabbitMQ"""
        connection = pika.BlockingConnection(pika.URLParameters(settings.RABBITMQ_URL))
        channel = connection.channel()
        channel.queue_declare(queue=settings.RABBITMQ_QUEUE_NAME, durable=True)

        message = {
            "contact_request_id": contact_request.id,
            "name": contact_request.name,
            "email": contact_request.email,
            "phone": contact_request.phone,
            "message": contact_request.message,
        }

        channel.basic_publish(
            exchange="",
            routing_key=settings.RABBITMQ_QUEUE_NAME,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
            ),
        )
        connection.close()
