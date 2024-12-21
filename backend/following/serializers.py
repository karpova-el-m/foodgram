from django.contrib.auth import get_user_model
from rest_framework import serializers

from recipes.serializers import RecipeShortSerializer
from .models import Follow

User = get_user_model()


class FollowSerializer(serializers.ModelSerializer):
    """Сериализатор для подписок."""
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(source='recipes.count')
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar'
        )

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        return user.following.filter(following=obj).exists()

    def get_recipes(self, obj):
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
        request = self.context['request']
        return request.build_absolute_uri(
            obj.avatar.url
        ) if obj.avatar else None


class FollowCreateSerializer(serializers.Serializer):
    """Сериализатор для создания подписки."""
    following = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all()
    )

    def validate_following(self, value):
        user = self.context['request'].user
        if value == user:
            raise serializers.ValidationError(
                'Вы не можете подписаться на самого себя.'
            )
        if user.following.filter(following=value).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого пользователя.'
            )
        return value

    def create(self, validated_data):
        following = validated_data['following']
        return Follow.objects.create(
            user=self.context['request'].user,
            following=following
        )

    def to_representation(self, instance):
        return FollowSerializer(
            instance.following,
            context=self.context
        ).data
