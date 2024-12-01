from django.db import models
from recipes.models import Recipe, User


class ShoppingList(models.Model):
    """Модель списка покупок для пользователя."""
    user = models.ForeignKey(
        User,
        related_name='shopping_list',
        on_delete=models.CASCADE
    )
    recipes = models.ManyToManyField(Recipe, related_name='shopping_list')

    def __str__(self):
        return f'Список покупок {self.user.username}'
