import logging

from django.contrib.auth import get_user_model
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.decorators import action
from rest_framework.pagination import (LimitOffsetPagination,
                                       PageNumberPagination)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from recipes.models import Ingredient, Recipe, Tag, Favorite
from .serializers import (
    IngredientSerializer, RecipeSerializer,
    UserRegistrationSerializer, UserSerializer,
    TagSerializer
)
from shopping_list.models import ShoppingList, ShoppingListItem

logging.basicConfig(level=logging.INFO)

User = get_user_model()


class RecipeViewSet(ModelViewSet):
    """Вьюсет для модели Recipe."""
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    pagination_class = LimitOffsetPagination
    permission_classes = [AllowAny]
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ('author', 'tags__name')
    search_fields = ('^author',)

    def get_permissions(self):
        """Задаёт разрешения для разных методов."""
        if self.action in ['create', 'partial_update']:
            return [IsAuthenticated()]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def validate_ingredients(self, ingredients):
        """Проверяет ингредиенты на уникальность и корректность."""
        ingredient_ids = [item['id'] for item in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError('Ингредиенты не могут повторяться.')
        ingredient_ids_from_db = [ingredient.id for ingredient in Ingredient.objects.all()]
        for ingredient_data in ingredients:
            ingredient_id = ingredient_data.get('id')
            if ingredient_id not in ingredient_ids_from_db:
                raise serializers.ValidationError(f'Ингредиент с id {ingredient_id} не найден в базе данных.')
        if not ingredients or not any(item.get('amount', 0) > 0 for item in ingredients):
            raise serializers.ValidationError('Укажите хотя бы один ингредиент с количеством больше 0.')

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
        if self.get_object().author != self.request.user:
            raise PermissionDenied('У вас нет прав на редактирование этого рецепта.')
        self.validate_ingredients(self.request.data.get('ingredients', []))
        self.validate_tags(self.request.data.get('tags', []))
        serializer.save()

    @action(
        detail=False,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='favorite'
    )
    def favorite(self, request):
        recipe = self.get_object()
        if request.method == 'POST':
            if Favorite.objects.filter(user=request.user, recipe=recipe).exists():
                return Response(
                    {'detail': 'Рецепт уже добавлен в избранное.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Favorite.objects.create(user=request.user, recipe=recipe)
            return Response(
                {'detail': 'Рецепт добавлен в избранное.'},
                status=status.HTTP_201_CREATED
            )
        elif request.method == 'DELETE':
            favorite = Favorite.objects.filter(user=request.user, recipe=recipe).first()
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
        permission_classes=[IsAuthenticated],
        url_path='shopping_cart'
    )
    def add_to_shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            shopping_list, created = ShoppingList.objects.get_or_create(
                user=request.user
            )
            shopping_list.recipes.add(recipe)
            shopping_list.save()
            for ingredient in recipe.ingredients.all():
                shopping_list_item, created = ShoppingListItem.objects.get_or_create(
                    shopping_list=shopping_list,
                    ingredient=ingredient,
                )
                if not created:
                    shopping_list_item.amount += ingredient.amount
                shopping_list_item.save()
            return Response({'detail': 'Рецепт добавлен в список покупок.'}, status=status.HTTP_200_OK)
        elif request.method == 'DELETE':
            shopping_list = ShoppingList.objects.filter(user=request.user).first()
            if not shopping_list:
                return Response({'detail': 'Список покупок не найден.'}, status=status.HTTP_404_NOT_FOUND)
            shopping_list.recipes.remove(recipe)
            for ingredient in recipe.ingredients.all():
                shopping_list_item = ShoppingListItem.objects.filter(shopping_list=shopping_list, ingredient=ingredient).first()
                if shopping_list_item:
                    shopping_list_item.delete()
            return Response({'detail': 'Рецепт удален из списка покупок.'}, status=status.HTTP_200_OK)


class IngredientViewSet(ReadOnlyModelViewSet):
    """Вьюсет для модели Ingredient."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ('name',)
    search_fields = ('^name',)


class TagsViewSet(ReadOnlyModelViewSet):
    """Вьюсет для модели Tag."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]


class UserViewSet(ModelViewSet):
    """Вьюсет для модели User."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = LimitOffsetPagination
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
        permission_classes=(IsAuthenticated, )
    )
    def profile_update(self, request):
        logging.info(f'Запрос от пользователя: {request.user}')
        if not request.user or not request.user.is_authenticated:
            logging.info(f'Пользователь не аутентифицирован. {request.user}')
            return Response({'detail': 'Пользователь не аутентифицирован.'}, status=status.HTTP_401_UNAUTHORIZED)
        if request.method == 'PATCH':
            serializer = UserSerializer(
                request.user, data=request.data, partial=True, context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            logging.info(f'Нов Данные пользователя: {serializer.data}')
            return Response(serializer.data, status=status.HTTP_200_OK)
        serializer = UserSerializer(self.request.user, context={'request': request})
        logging.info(f'Данные пользователя: {serializer.data}')
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['post'],
        permission_classes=[IsAuthenticated],
        url_path='set_password'
    )
    def set_password(self, request):
        user = request.user
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        if not user.check_password(current_password):
            return Response({'detail': 'Текущий пароль неверный.'}, status=status.HTTP_400_BAD_REQUEST)
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
        permission_classes=[IsAuthenticated],
        url_path='me/avatar'
    )
    def avatar(self, request):
        """Обновление или удаление аватара пользователя."""
        user = request.user
        if request.method == 'PUT':
            avatar = request.data.get('avatar')
            if not avatar:
                return Response(
                    {'detail': 'Base64 строка аватара не передана.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.avatar = avatar
            user.save()
            return Response({'avatar': avatar}, status=status.HTTP_200_OK)
        elif request.method == 'DELETE':
            user.avatar = None
            user.save()
            return Response(
                {'detail': 'Аватар успешно удален.'},
                status=status.HTTP_204_NO_CONTENT
            )
