import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import (BooleanFilter, CharFilter,
                                           DjangoFilterBackend, FilterSet)
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from .permissions import IsAuthorOrReadOnly
from recipes.models import Favorite, Ingredient, Recipe, Tag
from following.models import Follow
from .serializers import (AvatarSerializer, FollowSerializer,
                          IngredientSerializer, RecipeSerializer,
                          TagSerializer, UserRegistrationSerializer,
                          UserSerializer)
from shopping_list.models import ShoppingList

User = get_user_model()


class RecipeFilter(FilterSet):
    tags = CharFilter(method='filter_tags')
    is_favorited = BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = BooleanFilter(method='filter_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ('author',)

    def filter_tags(self, queryset, name, value):
        """Фильтрует рецепты по тегам, переданным в запросе."""
        tags = self.request.query_params.getlist('tags')
        if tags:
            queryset = queryset.filter(tags__name__in=tags).distinct()
        return queryset

    def filter_is_favorited(self, queryset, name, value):
        """
        Фильтрация по параметру is_favorited. Возвращает только те рецепты,
        которые находятся в избранном у текущего пользователя.
        """
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(favorites__user=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """
        Фильтрация по параметру is_in_shopping_cart. Возвращает только те
        рецепты, которые находятся в списке покупок текущего пользователя.
        """
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(shopping_list__user=user)
        return queryset


class RecipeViewSet(ModelViewSet):
    """Вьюсет для модели Recipe."""
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [AllowAny]
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_permissions(self):
        """Задает разрешения для разных методов."""
        if self.action in ['destroy', 'partial_update']:
            return [IsAuthorOrReadOnly()]
        elif self.action in ['create']:
            return [IsAuthenticated()]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def validate_ingredients(self, ingredients):
        """Проверяет ингредиенты на уникальность и корректность."""
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
        """Проверяет теги на уникальность и существование в базе данных."""
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

    def perform_update(self, serializer):
        self.validate_ingredients(self.request.data.get('ingredients', []))
        self.validate_tags(self.request.data.get('tags', []))
        serializer.save()

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,),
        url_path='favorite'
    )
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            if Favorite.objects.filter(
                user=request.user, recipe=recipe
            ).exists():
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
        elif request.method == 'DELETE':
            favorite = Favorite.objects.filter(
                user=request.user, recipe=recipe
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

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,),
        url_path='shopping_cart'
    )
    def shopping_cart(self, request, pk=None):
        """Добавление и удаление рецепта из списка покупок."""
        user = request.user
        shopping_list, created = ShoppingList.objects.get_or_create(user=user)
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            if shopping_list.recipes.filter(id=recipe.id).exists():
                return Response(
                    {'detail': 'Рецепт уже в списке покупок.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            shopping_list.recipes.add(recipe)
            return Response(
                {
                    'id': recipe.id,
                    'name': recipe.name,
                    'image': recipe.image.url,
                    'cooking_time': recipe.cooking_time
                },
                status=status.HTTP_201_CREATED
            )
        elif request.method == 'DELETE':
            if not shopping_list.recipes.filter(id=recipe.id).exists():
                return Response(
                    {'detail': 'Рецепт не найден в списке покупок.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            shopping_list.recipes.remove(recipe)
            return Response(
                {'detail': 'Рецепт удален из списка покупок.'},
                status=status.HTTP_204_NO_CONTENT
            )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(IsAuthenticated,),
        url_path='download_shopping_cart'
    )
    def download_shopping_cart(self, request):
        """Скачать список покупок."""
        user = request.user
        shopping_list = ShoppingList.objects.filter(user=user).first()
        if not shopping_list or not shopping_list.recipes.exists():
            return Response(
                {'detail': 'Список покупок пуст.'},
                status=status.HTTP_200_OK
            )
        ingredients_summary = {}
        for recipe in shopping_list.recipes.all():
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
            'attachment; filename="shopping_list.pdf"'
        )
        FONT_PATH = os.path.join(
            settings.BASE_DIR,
            'api',
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

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link'
    )
    def get_short_link(self, request, pk=None):
        """Возвращает короткую ссылку на рецепт."""
        base_url = getattr(settings, 'BASE_URL')
        short_link = f"{base_url}/{pk}/"
        return Response(
            {'short-link': short_link},
            status=status.HTTP_200_OK
        )


class IngredientViewSet(ReadOnlyModelViewSet):
    """Вьюсет для модели Ingredient."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    pagination_class = None
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ('name',)
    search_fields = ('^name',)


class TagsViewSet(ReadOnlyModelViewSet):
    """Вьюсет для модели Tag."""
    queryset = Tag.objects.all()
    pagination_class = None
    serializer_class = TagSerializer
    permission_classes = [AllowAny]


class UserViewSet(ModelViewSet):
    """Вьюсет для модели User."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    search_fields = ('username',)
    http_method_names = ['get', 'post', 'patch', 'put', 'delete']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'create']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserRegistrationSerializer
        return UserSerializer

    def create(self, request, *args, **kwargs):
        """
        Переопределение метода создания для использования
        UserRegistrationSerializer.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=False,
        url_path='me',
        methods=['get', 'patch', 'put'],
        permission_classes=(IsAuthorOrReadOnly,)
    )
    def profile_update(self, request):
        if not request.user or not request.user.is_authenticated:
            return Response(
                {'detail': 'Пользователь не аутентифицирован.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        if request.method == 'PATCH':
            serializer = UserSerializer(
                request.user, data=request.data, partial=True, context={
                    'request': request
                }
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        serializer = UserSerializer(
            self.request.user,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['post'],
        permission_classes=(IsAuthenticated,),
        url_path='set_password'
    )
    def set_password(self, request):
        user = request.user
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        if not user.check_password(current_password):
            return Response(
                {'detail': 'Текущий пароль неверный.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if new_password:
            user.set_password(new_password)
            user.save()
            return Response(
                {'detail': 'Пароль успешно обновлен.'},
                status=status.HTTP_204_NO_CONTENT
            )
        return Response(
            {'detail': 'Новый пароль не передан.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        detail=False,
        methods=['put', 'delete'],
        permission_classes=(IsAuthorOrReadOnly,),
        url_path='me/avatar'
    )
    def avatar(self, request):
        """Обновление или удаление аватара пользователя."""
        user = request.user
        if request.method == 'PUT':
            serializer = AvatarSerializer(request.user, data=request.data,
                                          context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif request.method == 'DELETE':
            user.avatar = None
            user.save()
            return Response(
                {'detail': 'Аватар успешно удален.'},
                status=status.HTTP_204_NO_CONTENT
            )

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,),
        url_path='subscribe'
    )
    def subscribe(self, request, pk=None):
        """
        Подписаться/отписаться от пользователя.
        """
        user_to_follow = get_object_or_404(User, pk=pk)
        if user_to_follow == request.user:
            return Response(
                {'detail': 'Вы не можете подписаться на самого себя.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if request.method == 'POST':
            if Follow.objects.filter(
                user=request.user,
                following=user_to_follow
            ).exists():
                return Response(
                    {'detail': 'Вы уже подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            Follow.objects.create(user=request.user, following=user_to_follow)
            serializer = FollowSerializer(
                user_to_follow,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            follow_instance = Follow.objects.filter(
                user=request.user,
                following=user_to_follow
            ).first()
            if not follow_instance:
                return Response(
                    {'detail': 'Вы не подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            follow_instance.delete()
            return Response(
                {'detail': 'Вы отписались от пользователя.'},
                status=status.HTTP_204_NO_CONTENT,
            )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path='subscriptions'
    )
    def subscriptions(self, request):
        """Возвращает список всех подписок пользователя."""
        subscriptions = Follow.objects.filter(
            user=request.user
        ).select_related('following')
        followed_users = [follow.following for follow in subscriptions]
        page = self.paginate_queryset(followed_users)
        if page is not None:
            serializer = FollowSerializer(
                page,
                many=True,
                context={'request': request}
            )
            return self.get_paginated_response(serializer.data)
        serializer = FollowSerializer(
            followed_users,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)
