from django.contrib.auth.models import AbstractUser
from django.db import models

from core.constants import MAX_LENGTH_FIRST_AND_LAST_NAME, MAX_LENGTH_USERNAME

from .validators import validate_username


class User(AbstractUser):
    """Модель User."""
    email = models.EmailField(unique=True,)
    username = models.CharField(
        max_length=MAX_LENGTH_USERNAME,
        validators=[validate_username],
        unique=True,
    )
    first_name = models.CharField(
        max_length=MAX_LENGTH_FIRST_AND_LAST_NAME,
    )
    last_name = models.CharField(
        max_length=MAX_LENGTH_FIRST_AND_LAST_NAME,
    )
    avatar = models.ImageField(
        upload_to='users/images/',
        null=True,
        blank=True,
        default=None
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
