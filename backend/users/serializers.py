import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from rest_framework import serializers

from core.constants import NON_VALID_USERNAME
from following.models import Follow

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """Сериализатор фотографий."""
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


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

    def validate(self, data):
        username = data.get('username').lower()
        if username == NON_VALID_USERNAME.lower():
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
