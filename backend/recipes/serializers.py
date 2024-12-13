from django.contrib.auth import get_user_model
from rest_framework import serializers

from core.fields import Base64ImageField
from recipes.models import Recipe, RecipeIngredient
from favorite.models import Favorite
from ingredients.models import Ingredient
from shopping_cart.models import ShoppingCart
from users.serializers import UserSerializer
from tags.serializers import TagSerializer

User = get_user_model()


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
            return ShoppingCart.objects.filter(
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
