from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from recipes.models import Recipe
from .models import Favorite
from .serializers import FavoriteSerializer


class FavoriteViewSet(ListModelMixin, GenericViewSet):
    """Вьюсет для работы с избранными рецептами."""
    queryset = Favorite.objects.all()
    serializer_class = FavoriteSerializer
    permission_classes = (IsAuthenticated,)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({
            'request': self.request,
            'view': self,
            'pk': self.kwargs.get('pk')
        })
        return context

    @action(
        detail=True,
        methods=['post'],
        url_path='favorite'
    )
    def add_to_favorite(self, request, pk=None):
        serializer = self.get_serializer(data={})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @add_to_favorite.mapping.delete
    def remove_from_favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        favorite = recipe.favorites.filter(user=request.user)
        if not favorite.exists():
            return Response(
                {'detail': 'Рецепт не найден в избранном.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        favorite.delete()
        return Response(
            {'detail': 'Рецепт удален из избранного.'},
            status=status.HTTP_204_NO_CONTENT,
        )
