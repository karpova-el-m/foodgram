from rest_framework import serializers

from .models import ShoppingCart
from recipes.models import Recipe


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
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )

    def validate(self, data):
        user = self.context['request'].user
        recipe = self.context['recipe']
        if recipe.shopping_cart.filter(user=user).exists():
            raise serializers.ValidationError(
                {'detail': 'Рецепт уже в списке покупок.'}
            )
        return data

    def create(self, validated_data):
        user = self.context['request'].user
        recipe = self.context['recipe']
        shopping_cart = ShoppingCart.objects.create(user=user, recipe=recipe)
        return shopping_cart


class RecipeShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для краткого отображения рецепта."""
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')

    def get_image(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.image.url) if obj.image else None
