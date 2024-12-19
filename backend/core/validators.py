import re
from re import sub

from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError

from core.constants import USER_NAME_REGEX


class CustomUsernameValidator(UnicodeUsernameValidator):
    """Кастомный валидатор для имени пользователя."""

    def __call__(self, value):
        if re.search(r'\bme\b', value, re.IGNORECASE):
            raise ValidationError(
                'Имя пользователя не может содержать "me" в любом написании.'
            )
        super().__call__(value)


def validate_username(value):
    if value in sub(USER_NAME_REGEX, "", value):
        raise ValidationError(
            message='Можно использовать латинские буквы и символы ., @, +, -.',
            params={'value': value},
        )


def validate_amount(value):
    if value < 0:
        raise ValidationError('Amount должен быть больше 0.')
