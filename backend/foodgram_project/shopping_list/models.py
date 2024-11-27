from django.db import models
from recipes.models import Recipe, Ingredient, User


class ShoppingList(models.Model):
    """Модель списка покупок для пользователя."""
    user = models.ForeignKey(User, related_name='shopping_list', on_delete=models.CASCADE)
    recipes = models.ManyToManyField(Recipe, related_name='shopping_list')

    def __str__(self):
        return f'Список покупок {self.user.username}'


class ShoppingListItem(models.Model):
    """Модель для элемента списка покупок (ингредиент)."""
    shopping_list = models.ForeignKey(ShoppingList, related_name='items', on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'{self.amount} {self.ingredient.measurement_unit} of {self.ingredient.name}'
