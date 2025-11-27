from django.db import models


class ContactRequest(models.Model):
    """Модель запроса на контакт"""

    name = models.CharField(max_length=200, verbose_name="Имя")
    email = models.EmailField(verbose_name="Email")
    phone = models.CharField(max_length=20, verbose_name="Телефон", blank=True)
    message = models.TextField(verbose_name="Сообщение", blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    processed = models.BooleanField(default=False, verbose_name="Обработано")

    class Meta:
        verbose_name = "Запрос на контакт"
        verbose_name_plural = "Запросы на контакт"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.email})"
