from django.db import models

from core.constants import MAX_LENGTH, MEASUREMENT_UNIT_CHOICES


class Ingredient(models.Model):
    """Модель Ингредиентов."""
    name = models.CharField(
        verbose_name='Название ингредиента',
        unique=True,
        max_length=MAX_LENGTH
    )
    measurement_unit = models.CharField(
        max_length=10,
        choices=MEASUREMENT_UNIT_CHOICES,
        verbose_name='Единица измерения'
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient_combination'
            )
        ]

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'
