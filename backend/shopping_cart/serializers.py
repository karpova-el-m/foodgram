from rest_framework import serializers

from .models import ShoppingCart


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для списка покупок."""
    name = serializers.ReadOnlyField(
        source='recipe.name'
    )
    image = serializers.ImageField(
        source='recipe.image',
        read_only=True
    )
    cooking_time = serializers.IntegerField(
        source='recipe.cooking_time',
        read_only=True
    )

    class Meta:
        model = ShoppingCart
        fields = ['id', 'name', 'image', 'cooking_time']

    def create(self, validated_data):
        shopping_cart = ShoppingCart.objects.create(**validated_data)
        return shopping_cart

    def update(self, instance, validated_data):
        recipes = validated_data.get('recipes', instance.recipes.all())
        instance.recipes.set(recipes)
        instance.save()
        return instance
