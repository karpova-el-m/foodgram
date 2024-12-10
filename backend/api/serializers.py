from django.contrib.auth import get_user_model
from rest_framework import serializers

from core.fields import Base64ImageField
from recipes.models import Favorite, Ingredient, Recipe, RecipeIngredient, Tag
from shopping_list.models import ShoppingList
from users.serializers import UserSerializer

User = get_user_model()


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор объекта ингредиент."""
    amount = serializers.SerializerMethodField()

    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measurement_unit', 'amount']

    def get_amount(self, obj):
        recipe_id = self.context.get('recipe_id')
        if recipe_id:
            recipe_ingredient = RecipeIngredient.objects.filter(
                recipe_id=recipe_id, ingredient=obj
            ).first()
            if recipe_ingredient:
                amount = recipe_ingredient.amount
                return amount

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if not self.context.get('recipe_id'):
            representation.pop('amount', None)
        return representation


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор объекта тег."""
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор объекта рецепт."""
    ingredients = serializers.SerializerMethodField()
    author = UserSerializer(read_only=True)
    tags = TagSerializer(read_only=True, many=True)
    image = Base64ImageField(required=True, allow_null=False)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [
            'id',
            'author',
            'name',
            'text',
            'cooking_time',
            'image',
            'tags',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart'
        ]

    def get_ingredients(self, obj):
        recipe_ingredients = RecipeIngredient.objects.filter(recipe=obj)
        return [
            {
                'id': ri.ingredient.id,
                'name': ri.ingredient.name,
                'measurement_unit': ri.ingredient.measurement_unit,
                'amount': ri.amount,
            }
            for ri in recipe_ingredients
        ]

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(
                user=request.user, recipe=obj
            ).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ShoppingList.objects.filter(
                user=request.user, recipes=obj
            ).exists()
        return False

    def create(self, validated_data):
        tags_data = self.initial_data.get('tags')
        ingredients_data = self.initial_data.get('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        if tags_data:
            recipe.tags.set(tags_data)
        if ingredients_data:
            for ingredient_data in ingredients_data:
                ingredient = Ingredient.objects.get(id=ingredient_data['id'])
                RecipeIngredient.objects.create(
                    recipe=recipe,
                    ingredient=ingredient,
                    amount=ingredient_data['amount']
                )
        return recipe


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов, добавленных в избранное."""
    class Meta:
        model = Favorite
        fields = ['id', 'name', 'image', 'cooking_time']
        read_only_fields = ['name', 'image', 'cooking_time']

    def create(self, validated_data):
        """Создание записи о добавлении рецепта в избранное."""
        user = self.context['request'].user
        recipe = validated_data['recipe']
        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError('Этот рецепт уже в избранном.')
        return Favorite.objects.create(user=user, **validated_data)


class RecipeShortSerializer(serializers.ModelSerializer):
    """
    Упрощенный сериализатор рецепта из подписок.
    """
    class Meta:
        model = Recipe
        fields = [
            'id',
            'name',
            'image',
            'cooking_time'
        ]
