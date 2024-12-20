from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from core.fields import Base64ImageField
from favorite.models import Favorite
from recipes.models import Recipe, RecipeIngredient
from shopping_cart.models import ShoppingCart
from tags.models import Tag
from tags.serializers import TagSerializer
from users.serializers import UserSerializer
from core.constants import MIN_COOK_TIME, MAX_COOK_TIME
from ingredients.models import Ingredient

User = get_user_model()


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов в рецепте."""
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        read_only=True
    )
    amount = serializers.SerializerMethodField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')

    def get_amount(self, obj):
        return float(obj.amount)


class RecipeIngredientUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления ингредиентов в рецепте."""
    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор объекта рецепт."""
    tags = TagSerializer(read_only=True, many=True)
    ingredients = RecipeIngredientSerializer(
        source='amount_ingredients',
        many=True,
        read_only=True
    )
    author = UserSerializer(read_only=True)
    image = Base64ImageField(required=True, allow_null=False)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
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
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        return (
            request.user.is_authenticated
            and Favorite.objects.filter(
                user=request.user,
                recipe=obj
            ).exists()
            if request else False
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        return (
            request.user.is_authenticated
            and ShoppingCart.objects.filter(
                user=request.user,
                recipe=obj
            ).exists()
            if request else False
        )


class RecipeShortSerializer(serializers.ModelSerializer):
    """Упрощенный сериализатор рецепта."""
    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления и создания рецепта."""
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientUpdateSerializer(many=True)
    image = Base64ImageField(required=True)
    cooking_time = serializers.IntegerField(
        min_value=MIN_COOK_TIME,
        max_value=MAX_COOK_TIME,
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError(
                'Укажите хотя бы один ингредиент.'
            )
        ingredient_ids = [item['id'] for item in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Ингредиенты не могут повторяться.'
            )
        existing_ingredient_ids = set(
            Ingredient.objects.filter(id__in=ingredient_ids).values_list(
                'id',
                flat=True
            )
        )
        for ingredient_data in ingredients:
            if ingredient_data['id'] not in existing_ingredient_ids:
                raise serializers.ValidationError(
                    f'Ингредиент с id={ingredient_data["id"]} не найден.'
                )
        for ingredient in ingredients:
            if int(ingredient.get('amount', 0)) <= 0:
                raise serializers.ValidationError(
                    'Количество ингредиента должно быть больше 0.'
                )
        return ingredients

    def validate_tags(self, tags):
        if not tags:
            raise serializers.ValidationError(
                'Рецепт должен содержать хотя бы один тег.'
            )
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(
                'Теги не могут повторяться.'
            )
        return tags

    def create_ingredients(self, ingredients, recipe):
        RecipeIngredient.objects.bulk_create([RecipeIngredient(
            recipe=recipe,
            ingredient_id=ingredient['id'],
            amount=ingredient['amount'],
        ) for ingredient in ingredients])

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        ingredients = validated_data.pop('ingredients', None)
        if tags is None or not tags:
            raise ValidationError('Теги обязательны для обновления.')
        if ingredients is None or not ingredients:
            raise ValidationError('Ингредиенты обязательны для обновления.')
        instance.tags.set(tags)
        instance.amount_ingredients.all().delete()
        self.create_ingredients(ingredients, instance)
        super().update(instance, validated_data)
        return instance

    def to_representation(self, instance):
        context = {'request': self.context.get('request')}
        return RecipeSerializer(instance, context=context).data
