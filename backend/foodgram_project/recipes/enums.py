from enum import Enum


class UserRoles(Enum):
    """Класс-перечисление для выбора пользовательских ролей."""

    user = 'user'
    admin = 'admin'

    @classmethod
    def choices(cls):
        """Формирует соответствие констант и значений."""
        return tuple((attribute.name, attribute.value) for attribute in cls)

    @classmethod
    def max_length_field(cls):
        """Формирует максимальную длину поля для модели."""
        return max(len(attribute.value) for attribute in cls)
