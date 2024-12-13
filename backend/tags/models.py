from django.contrib.auth import get_user_model
from django.db import models

from core.constants import MAX_LENGTH

User = get_user_model()


class Tag(models.Model):
    """Модель Tag."""
    name = models.CharField(
        verbose_name='Тег',
        unique=True,
        max_length=MAX_LENGTH
    )
    slug = models.SlugField(
        unique=True,
        verbose_name='Идентификатор',
        help_text=(
            'Идентификатор страницы для URL; '
            'разрешены символы латиницы, цифры, дефис и подчеркивание.'
        ),
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name
