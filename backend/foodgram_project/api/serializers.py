import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from foodgram_project.constants import NON_VALID_USERNAME
from rest_framework import serializers

from shopping_list.models import ShoppingList
from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag, Favorite
from following.models import Follow

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """Сериализатор аватара."""
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


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


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации user."""
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор объекта юзер."""
    is_subscribed = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True, required=False)
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'avatar',
            'is_subscribed',
            'password'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def get_is_subscribed(self, obj):
        """
        Проверяет, подписан ли текущий пользователь на данного пользователя.
        Возвращает True, если подписан, иначе False.
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Follow.objects.filter(user=request.user, following=obj).exists()
        return False

    def validate(self, data):
        if data.get('username') == NON_VALID_USERNAME:
            raise serializers.ValidationError(
                f'Использовать имя "{NON_VALID_USERNAME}" запрещено'
            )
        if User.objects.filter(username=data.get('username')).exists():
            raise serializers.ValidationError(
                'Пользователь с таким username уже существует'
            )
        if User.objects.filter(email=data.get('email')).exists():
            raise serializers.ValidationError(
                'Пользователь с таким email уже существует'
            )
        return data

    def update(self, instance, validated_data):
        """Обновление данных пользователя (без изменения пароля)."""
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        avatar_data = validated_data.get('avatar', None)
        if avatar_data:
            instance.avatar = avatar_data
            return super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user


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
                "id": ri.ingredient.id,
                "name": ri.ingredient.name,
                "measurement_unit": ri.ingredient.measurement_unit,
                "amount": ri.amount,
            }
            for ri in recipe_ingredients
        ]

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(user=request.user, recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ShoppingList.objects.filter(user=request.user, recipes=obj).exists()
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
