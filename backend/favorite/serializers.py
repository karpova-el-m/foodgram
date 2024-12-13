from rest_framework import serializers
from django.shortcuts import get_object_or_404

from .models import Favorite
from recipes.models import Recipe


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов, добавленных в избранное."""
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
        model = Favorite
        fields = ['id', 'name', 'image', 'cooking_time']
        read_only_fields = ['name', 'image', 'cooking_time']

    def create(self, validated_data):
        """Создание записи о добавлении рецепта в избранное."""
        user = self.context['request'].user
        recipe_id = self.context['view'].kwargs.get('recipe_id')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        if not Recipe.objects.filter(id=recipe.id).exists():
            raise serializers.ValidationError('Рецепт не найден.')
        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError('Этот рецепт уже в избранном.')
        return Favorite.objects.create(user=user, recipe=recipe)
