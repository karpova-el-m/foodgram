from django.contrib.auth import get_user_model

from .models import Follow

User = get_user_model()


def is_subscribed(self, user):
    """Проверяет, подписан ли текущий пользователь на `user`."""
    return Follow.objects.filter(user=self, following=user).exists()


def followings(self):
    """Возвращает список пользователей, на которых подписан пользователь."""
    return Follow.objects.filter(user=self)


User.add_to_class('is_following', is_subscribed)
User.add_to_class('followings', followings)
