from rest_framework import serializers
from .models import ShoppingList, ShoppingListItem


class ShoppingListItemSerializer(serializers.ModelSerializer):
    """Сериализатор для элемента списка покупок (ингредиента)."""
    class Meta:
        model = ShoppingListItem
        fields = ['ingredient', 'amount']


class ShoppingListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка покупок."""
    items = ShoppingListItemSerializer(many=True, read_only=True)

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
                shopping_list_item, created = ShoppingListItem.objects.get_or_create(
                    shopping_list=shopping_list,
                    ingredient=ingredient,
                )
                shopping_list_item.amount += ingredient.amount
                shopping_list_item.save()
