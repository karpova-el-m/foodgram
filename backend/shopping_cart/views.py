from django.db.models import Sum
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import CreateModelMixin, DestroyModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from core.utils import generate_shopping_cart_pdf
from recipes.models import Recipe, RecipeIngredient
from .models import ShoppingCart
from .serializers import ShoppingCartSerializer


class ShoppingCartViewSet(CreateModelMixin, DestroyModelMixin, GenericViewSet):
    """Вьюсет для работы со списком покупок."""
    serializer_class = ShoppingCartSerializer

    @action(
        detail=True,
        methods=['post'],
        permission_classes=(IsAuthenticated,),
        url_path='shopping_cart'
    )
    def add_to_shopping_cart(self, request, pk=None):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        _, created = ShoppingCart.objects.get_or_create(
            user=user,
            recipe=recipe
        )
        if not created:
            return Response(
                {'detail': 'Рецепт уже в списке покупок.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            {
                'id': recipe.id,
                'name': recipe.name,
                'image': request.build_absolute_uri(recipe.image.url),
                'cooking_time': recipe.cooking_time
            },
            status=status.HTTP_201_CREATED
        )

    @add_to_shopping_cart.mapping.delete
    def remove_from_shopping_cart(self, request, pk=None):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        shopping_cart_item = ShoppingCart.objects.filter(
            user=user,
            recipe=recipe
        ).first()
        if not shopping_cart_item:
            return Response(
                {'detail': 'Рецепт не найден в списке покупок.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        shopping_cart_item.delete()
        return Response(
            {'detail': 'Рецепт успешно удален из списка покупок.'},
            status=status.HTTP_204_NO_CONTENT
        )


class DownloadShoppingCartView(APIView):
    """APIView для скачивания списка покупок."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Скачать список покупок."""
        user = request.user
        shopping_cart = ShoppingCart.objects.filter(user=user).first()
        if not shopping_cart:
            return Response(
                {'detail': 'Список покупок пуст.'},
                status=200
            )
        ingredients_summary = (
            RecipeIngredient.objects
            .filter(recipe__shopping_cart__user=user)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total_amount=Sum('amount'))
        )
        return generate_shopping_cart_pdf(user, ingredients_summary)
