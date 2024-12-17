from django.conf import settings
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from core.filters import RecipeFilter
from core.paginators import CustomPagination
from core.permissions import IsAuthorOrReadOnly
from ingredients.models import Ingredient
from tags.models import Tag
from .models import Recipe
from .serializers import RecipeCreateUpdateSerializer, RecipeSerializer

User = get_user_model()


class RecipeViewSet(ModelViewSet):
    """Вьюсет для модели Recipe."""
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [AllowAny]
    http_method_names = ['get', 'post', 'patch', 'delete']
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = CustomPagination

    def get_permissions(self):
        if self.action in ['destroy', 'partial_update']:
            return [IsAuthorOrReadOnly()]
        elif self.action in ['create']:
            return [IsAuthenticated()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action in ['create', 'partial_update']:
            return RecipeCreateUpdateSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def validate_ingredients(self, ingredients):
        ingredient_ids = [item['id'] for item in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Ингредиенты не могут повторяться.'
            )
        ingredient_ids_from_db = [
            ingredient.id for ingredient in Ingredient.objects.all()
        ]
        for ingredient_data in ingredients:
            ingredient_id = ingredient_data.get('id')
            if ingredient_id not in ingredient_ids_from_db:
                raise serializers.ValidationError(
                    f'Ингредиент с id {ingredient_id} не найден в базе данных.'
                )
        if not ingredients or not any(
            (lambda x: int(
                x.get('amount', 0)
            ) > 0)(item) for item in ingredients
        ):
            raise serializers.ValidationError(
                'Укажите хотя бы один ингредиент с количеством больше 0.'
            )

    def validate_tags(self, tags):
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(
                'Теги не могут повторяться.'
            )
        if not tags:
            raise serializers.ValidationError(
                'Рецепт должен содержать хотя бы один тег.'
            )
        tags_from_db = [tag.id for tag in Tag.objects.all()]
        for tag in tags:
            if tag not in tags_from_db:
                raise serializers.ValidationError(
                    f'Тег с id {tag} не найден в базе данных.'
                )

    def create(self, request, *args, **kwargs):
        self.validate_ingredients(request.data.get('ingredients', []))
        self.validate_tags(request.data.get('tags', []))
        return super().create(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        self.validate_ingredients(request.data.get('ingredients', []))
        self.validate_tags(request.data.get('tags', []))
        return super().partial_update(request, *args, **kwargs)

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link'
    )
    def get_short_link(self, request, pk=None):
        base_url = getattr(settings, 'BASE_URL')
        short_link = f'{base_url}/{pk}/'
        return Response(
            {'short-link': short_link},
            status=status.HTTP_200_OK
        )
