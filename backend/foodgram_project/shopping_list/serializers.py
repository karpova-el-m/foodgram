from rest_framework import serializers

from .models import ShoppingList, ShoppingListItem


class ShoppingListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка покупок."""

    class Meta:
        model = ShoppingList
        fields = ['id', 'name', 'image', 'cooking_time']

    def create(self, validated_data):
        shopping_list = super().create(validated_data)
        self.add_recipes_to_shopping_list(shopping_list)
        return shopping_list

    def add_recipes_to_shopping_list(self, shopping_list):
        recipes = shopping_list.recipes.all()
        for recipe in recipes:
            for ingredient in recipe.ingredients.all():
                shop_item, created = ShoppingListItem.objects.get_or_create(
                    shopping_list=shopping_list,
                    ingredient=ingredient,
                )
                shop_item.amount += ingredient.amount
                shop_item.save()
