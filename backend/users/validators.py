from re import sub

from django.core.exceptions import ValidationError

from core.constants import USER_NAME_REGEX


def validate_username(value):
    if value in sub(USER_NAME_REGEX, "", value):
        raise ValidationError(
            message='Можно использовать латинские буквы и символы ., @, +, -.',
            params={"value": value},
        )
