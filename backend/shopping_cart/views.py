import os

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from recipes.models import Recipe

from .models import ShoppingCart
from .serializers import ShoppingCartSerializer


class ShoppingCartViewSet(ModelViewSet):
    """Вьюсет для работы со списком покупок."""
    serializer_class = ShoppingCartSerializer

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,),
        url_path='shopping_cart'
    )
    def shopping_cart(self, request, pk=None):
        """Добавление и удаление рецепта из списка покупок."""
        user = request.user
        shopping_cart, created = ShoppingCart.objects.get_or_create(user=user)
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            if shopping_cart.recipes.filter(id=recipe.id).exists():
                return Response(
                    {'detail': 'Рецепт уже в списке покупок.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            shopping_cart.recipes.add(recipe)
            serializer = self.get_serializer(shopping_cart)
            return Response(
                {
                    "id": recipe.id,
                    "name": recipe.name,
                    "image": request.build_absolute_uri(recipe.image.url),
                    "cooking_time": recipe.cooking_time
                },
                status=status.HTTP_201_CREATED
            )
        elif request.method == 'DELETE':
            if not shopping_cart.recipes.filter(id=recipe.id).exists():
                return Response(
                    {'detail': 'Рецепт не найден в списке покупок.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            shopping_cart.recipes.remove(recipe)
            serializer = self.get_serializer(shopping_cart)
            return Response(
                serializer.data,
                status=status.HTTP_204_NO_CONTENT
            )


class DownloadShoppingCartView(APIView):
    """APIView для скачивания списка покупок."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Скачать список покупок."""
        user = request.user
        shopping_cart = ShoppingCart.objects.filter(user=user).first()
        if not shopping_cart or not shopping_cart.recipes.exists():
            return Response(
                {'detail': 'Список покупок пуст.'},
                status=200
            )
        ingredients_summary = {}
        for recipe in shopping_cart.recipes.all():
            for ingredient_data in recipe.recipeingredient_set.all():
                ingredient = ingredient_data.ingredient
                ingredient_id = ingredient.id
                if ingredient_id in ingredients_summary:
                    ingredients_summary[ingredient_id][
                        'amount'
                    ] += ingredient_data.amount
                else:
                    ingredients_summary[ingredient_id] = {
                        'name': ingredient.name,
                        'measurement_unit': ingredient.measurement_unit,
                        'amount': ingredient_data.amount
                    }
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_cart.pdf"'
        )
        FONT_PATH = os.path.join(
            settings.BASE_DIR,
            'fonts',
            'Stamps.ttf'
        )
        pdfmetrics.registerFont(TTFont('Stamps', FONT_PATH))
        pdf_canvas = canvas.Canvas(response, pagesize=A4)
        pdf_canvas.setFont('Stamps', 12)
        width, height = A4
        pdf_canvas.drawString(
            50, height - 50,
            f'Список покупок для {user.username}'
        )
        y_position = height - 100
        for ingr in ingredients_summary.values():
            line = (
                f"{ingr['name']} - {ingr['amount']} {ingr['measurement_unit']}"
            )
            pdf_canvas.drawString(50, y_position, line)
            y_position -= 20
            if y_position < 50:
                pdf_canvas.showPage()
                pdf_canvas.setFont('Stamps', 12)
                y_position = height - 50
        pdf_canvas.save()
        return response
