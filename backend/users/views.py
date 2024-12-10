from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from core.paginators import CustomPagination
from core.permissions import IsAuthorOrReadOnly
from following.models import Follow

from .serializers import (AvatarSerializer, 
                          UserRegistrationSerializer, UserSerializer)
from following.serializers import FollowSerializer

User = get_user_model()


class UserViewSet(ModelViewSet):
    """Вьюсет для модели User."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    search_fields = ('username',)
    pagination_class = CustomPagination
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
