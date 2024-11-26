import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from following.models import Follow
from foodgram_project.constants import NON_VALID_USERNAME
from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from rest_framework import serializers

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
                return recipe_ingredient.amount
        return None


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор объекта тег."""
    class Meta:
        model = Tag
        fields = '__all__'


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
    author.is_subscribed = serializers.SerializerMethodField()
    tags = TagSerializer(read_only=True, many=True)

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
            'ingredients'
        ]

    def get_ingredients(self, obj):
        """
        Возвращает ингредиеты определенного рецепта.
        """
        ingredients = obj.ingredients.all()
        serializer = IngredientSerializer(ingredients, many=True, context={'recipe_id': obj.id})
        return serializer.data


# class TokenSerializer(serializers.Serializer):
#     email = serializers.CharField(
#         label='Email',
#         write_only=True)
#     password = serializers.CharField(
#         label='Пароль',
#         style={'input_type': 'password'},
#         trim_whitespace=False,
#         write_only=True)
#     token = serializers.CharField(
#         label='Токен',
#         read_only=True)

#     def validate(self, attrs):
#         email = attrs.get('email')
#         password = attrs.get('password')
#         if email and password:
#             user = authenticate(
#                 request=self.context.get('request'),
#                 email=email,
#                 password=password)
#             if not user:
#                 raise serializers.ValidationError(
#                     'Не удается войти в систему с предоставленными учетными данными.',
#                     code='authorization')
#         else:
#             msg = 'Необходимо указать "адрес электронной почты" и "пароль".'
#             raise serializers.ValidationError(
#                 msg,
#                 code='authorization')
#         attrs['user'] = user
#         return attrs
