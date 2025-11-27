from django.core.validators import MinValueValidator
from django.db import models


class Product(models.Model):
    """Модель продукции (краски)"""

    name = models.CharField(max_length=200, verbose_name="Название")
    description = models.TextField(verbose_name="Описание (Markdown)")
    price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], verbose_name="Стоимость"
    )
    image = models.ImageField(
        upload_to="products/", verbose_name="Изображение", null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Продукция"
        verbose_name_plural = "Продукция"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
