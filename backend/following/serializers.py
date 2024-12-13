from django.contrib.auth import get_user_model
from rest_framework import serializers

from recipes.serializers import RecipeShortSerializer

User = get_user_model()


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
