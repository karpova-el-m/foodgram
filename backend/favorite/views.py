from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import CreateModelMixin, DestroyModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from recipes.models import Recipe
from .models import Favorite


class FavoriteViewSet(CreateModelMixin, DestroyModelMixin, GenericViewSet):
    """Вьюсет для работы с избранными рецептами."""

    @action(
        detail=True,
        methods=['post'],
        permission_classes=(IsAuthenticated,),
        url_path='favorite'
    )
    def add_to_favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        if Favorite.objects.filter(user=request.user, recipe=recipe).exists():
            return Response(
                {'detail': 'Рецепт уже добавлен в избранное.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        Favorite.objects.create(user=request.user, recipe=recipe)
        return Response(
            {
                'id': recipe.id,
                'name': recipe.name,
                'image': request.build_absolute_uri(recipe.image.url),
                'cooking_time': recipe.cooking_time,
            },
            status=status.HTTP_201_CREATED
        )

    @add_to_favorite.mapping.delete
    def remove_from_favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        favorite = Favorite.objects.filter(
            user=request.user,
            recipe=recipe
        ).first()
        if not favorite:
            return Response(
                {'detail': 'Рецепт не найден в избранном.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        favorite.delete()
        return Response(
            {'detail': 'Рецепт удален из избранного.'},
            status=status.HTTP_204_NO_CONTENT
        )
