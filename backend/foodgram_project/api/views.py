import logging

from django.contrib.auth import get_user_model
from recipes.models import Ingredient, Recipe
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.pagination import (LimitOffsetPagination,
                                       PageNumberPagination)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from .serializers import (IngredientSerializer, RecipeSerializer,
                          UserRegistrationSerializer, UserSerializer)

logging.basicConfig(level=logging.INFO)

User = get_user_model()


class RecipeViewSet(ModelViewSet):
    """Вьюсет для модели Recipe."""
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    pagination_class = PageNumberPagination
    permission_classes = [AllowAny]
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class IngredientViewSet(ReadOnlyModelViewSet):
    """Вьюсет для модели Ingredient."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer


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
