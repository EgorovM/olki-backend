import json
import time

import pika
from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand

from contacts.models import ContactRequest


class Command(BaseCommand):
    help = "Run RabbitMQ consumer for email notifications"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting RabbitMQ consumer..."))

        while True:
            try:
                connection = pika.BlockingConnection(pika.URLParameters(settings.RABBITMQ_URL))
                channel = connection.channel()
                channel.queue_declare(queue=settings.RABBITMQ_QUEUE_NAME, durable=True)

                self.stdout.write(self.style.SUCCESS("Waiting for messages. To exit press CTRL+C"))

                def callback(ch, method, _properties, body):
                    try:
                        message = json.loads(body)
                        self.process_message(message)
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                        self.stdout.write(self.style.SUCCESS(f"Processed message: {message}"))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"Error processing message: {e}"))
                        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

                channel.basic_qos(prefetch_count=1)
                channel.basic_consume(
                    queue=settings.RABBITMQ_QUEUE_NAME, on_message_callback=callback
                )

                channel.start_consuming()
            except pika.exceptions.AMQPConnectionError:
                self.stdout.write(
                    self.style.WARNING("RabbitMQ connection failed. Retrying in 5 seconds...")
                )
                time.sleep(5)
            except KeyboardInterrupt:
                self.stdout.write(self.style.SUCCESS("Stopping consumer..."))
                if "channel" in locals():
                    channel.stop_consuming()
                if "connection" in locals():
                    connection.close()
                break

    def process_message(self, message):
        """Обработать сообщение: отправить письма"""
        contact_request_id = message.get("contact_request_id")
        name = message.get("name")
        email = message.get("email")
        phone = message.get("phone", "")
        user_message = message.get("message", "")

        # Отправляем письмо пользователю с благодарностью
        self.send_thank_you_email(name, email)

        # Отправляем уведомление сервисным учеткам
        self.send_service_notification(name, email, phone, user_message)

        # Помечаем запрос как обработанный
        try:
            contact_request = ContactRequest.objects.get(id=contact_request_id)
            contact_request.processed = True
            contact_request.save()
        except ContactRequest.DoesNotExist:
            self.stdout.write(self.style.WARNING(f"ContactRequest {contact_request_id} not found"))

    def send_thank_you_email(self, name, email):
        """Отправить письмо с благодарностью пользователю"""
        subject = "Спасибо за ваш запрос!"
        message = f"""
Здравствуйте, {name}!

Спасибо за ваш интерес к нашей продукции. Мы получили ваш запрос и свяжемся с вами в ближайшее время.

С уважением,
Команда OLKI Paint
        """
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )

    def send_service_notification(self, name, email, phone, user_message):
        """Отправить уведомление сервисным учеткам о новом заказе"""
        subject = f"Новый запрос на контакт от {name}"
        message = f"""
Поступил новый запрос на контакт:

Имя: {name}
Email: {email}
Телефон: {phone or "не указан"}
Сообщение: {user_message or "не указано"}

Пожалуйста, свяжитесь с клиентом в ближайшее время.
        """
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [settings.SERVICE_EMAIL],
            fail_silently=False,
        )
