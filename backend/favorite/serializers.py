from django.shortcuts import get_object_or_404
from rest_framework import serializers

from recipes.models import Recipe
from .models import Favorite


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
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )
        read_only_fields = (
            'name',
            'image',
            'cooking_time'
        )

    def validate(self, attrs):
        user = self.context['request'].user
        recipe_id = self.context['view'].kwargs.get('pk')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        if recipe.favorites.filter(user=user).exists():
            raise serializers.ValidationError('Этот рецепт уже в избранном.')
        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        recipe_id = self.context['view'].kwargs.get('pk')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        return Favorite.objects.create(user=user, recipe=recipe)
