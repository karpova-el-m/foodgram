from django.db.models import Sum
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import HttpResponse

from core.utils import ShoppingCartPDFGenerator
from recipes.models import Recipe, RecipeIngredient
from .models import ShoppingCart
from .serializers import ShoppingCartSerializer, RecipeShoppingCartSerializer


class ShoppingCartView(APIView):
    """APIView для работы со списком покупок."""
    permission_classes = (IsAuthenticated,)

    def post(self, request, pk=None):
        serializer = ShoppingCartSerializer(
            data=request.data,
            context={
                'request': request,
                'recipe': get_object_or_404(Recipe, pk=pk)
            }
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        response_serializer = RecipeShoppingCartSerializer(
            get_object_or_404(Recipe, pk=pk),
            context={'request': request}
        )
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED
        )

    def delete(self, request, pk=None):
        shopping_cart = get_object_or_404(Recipe, pk=pk).shopping_cart.filter(
            user=request.user
        )
        if not shopping_cart.exists():
            return Response(
                {'detail': 'Рецепт не найден в списке покупок.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        shopping_cart.delete()
        return Response(
            {'detail': 'Рецепт успешно удален из списка покупок.'},
            status=status.HTTP_204_NO_CONTENT
        )


class DownloadShoppingCartView(APIView):
    """APIView для скачивания списка покупок."""
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        """Скачать список покупок."""
        if not ShoppingCart.objects.filter(user=request.user).exists():
            return Response(
                {'detail': 'Список покупок пуст.'},
                status=200
            )
        ingredients_summary = (
            RecipeIngredient.objects
            .filter(recipe__shopping_cart__user=request.user)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total_amount=Sum('amount'))
        )
        pdf_generator = ShoppingCartPDFGenerator(
            request.user,
            ingredients_summary
        )
        pdf_data = pdf_generator.generate()
        response = HttpResponse(pdf_data, content_type='application/pdf')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_cart.pdf"'
        )
        return response
