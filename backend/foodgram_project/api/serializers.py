import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from rest_framework import serializers

from following.models import Follow
from foodgram_project.constants import NON_VALID_USERNAME
from recipes.models import Favorite, Ingredient, Recipe, RecipeIngredient, Tag
from shopping_list.models import ShoppingList

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """Сериализатор фотографий."""
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
        fields = [
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'password'
        ]

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(allow_null=True)

    class Meta:
        model = User
        fields = [
            'avatar',
        ]


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор объекта юзер."""
    is_subscribed = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True)
    # avatar = Base64ImageField(required=False, allow_null=True)

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
            return Follow.objects.filter(
                user=request.user, following=obj
            ).exists()
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
        avatar = validated_data.pop('avatar', None)
        if avatar:
            if isinstance(avatar, str) and avatar.startswith('data:image'):
                avatar_field = Base64ImageField()
                avatar = avatar_field.to_internal_value(avatar)
            instance.avatar = avatar
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if password:
            instance.set_password(password)
            instance.save()
        return instance


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


class FollowSerializer(serializers.ModelSerializer):
    """Сериализатор для подписок."""
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(source='recipes.count')
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar'
        ]

    def get_is_subscribed(self, obj):
        """
        Определяет, подписан ли текущий пользователь на пользователя.
        """
        user = self.context['request'].user
        return user.following.filter(following=obj).exists()

    def get_recipes(self, obj):
        """Получает список рецептов пользователя."""
        request = self.context['request']
        try:
            recipes_limit = int(request.query_params.get('recipes_limit', 0))
            if recipes_limit < 0:
                recipes_limit = 0
        except ValueError:
            recipes_limit = 0
        recipes = obj.recipes.all()
        if recipes_limit:
            recipes = recipes[:recipes_limit]
        return RecipeShortSerializer(
            recipes,
            many=True,
            context=self.context
        ).data

    def get_avatar(self, obj):
        """
        Получает полный URL для аватара пользователя.
        """
        request = self.context['request']
        return request.build_absolute_uri(
            obj.avatar.url
        ) if obj.avatar else None
