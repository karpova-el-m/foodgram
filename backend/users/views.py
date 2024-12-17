from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from core.mixins import UpdateModelMixin
from core.paginators import CustomPagination
from core.permissions import IsAuthorOrReadOnly
from following.models import Follow
from following.serializers import FollowSerializer
from .serializers import (AvatarSerializer, SetPasswordSerializer,
                          UserRegistrationSerializer, UserSerializer)

User = get_user_model()


class UserViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    UpdateModelMixin,
    viewsets.GenericViewSet
):
    """Вьюсет для модели User."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    search_fields = ('username',)
    pagination_class = CustomPagination
    http_method_names = ['get', 'post', 'patch', 'put', 'delete']

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'create'):
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_user_serializer(self, user):
        return UserSerializer(user, context={'request': self.request})

    def get_follow_serializer(self, user, data=None, partial=False):
        return FollowSerializer(user, context={'request': self.request})

    def get_serializer_class(self):
        if self.action == 'create':
            return UserRegistrationSerializer
        return UserSerializer

    @action(
        detail=False,
        url_path='me',
        methods=['get'],
        permission_classes=(IsAuthorOrReadOnly,)
    )
    def retrieve_profile(self, request):
        serializer = self.get_user_serializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['post'],
        permission_classes=(IsAuthenticated,),
        url_path='set_password'
    )
    def set_password(self, request):
        serializer = SetPasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {'detail': 'Пароль успешно обновлен.'},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(
        detail=False,
        methods=['put'],
        permission_classes=(IsAuthorOrReadOnly,),
        url_path='me/avatar'
    )
    def update_avatar(self, request):
        serializer = AvatarSerializer(
            request.user,
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @update_avatar.mapping.delete
    def delete_avatar(self, request):
        request.user.avatar = None
        request.user.save()
        return Response(
            {'detail': 'Аватар успешно удален.'},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(
        detail=True,
        methods=['post'],
        permission_classes=(IsAuthenticated,),
        url_path='subscribe'
    )
    def subscribe(self, request, pk=None):
        user_to_follow = get_object_or_404(User, pk=pk)
        if user_to_follow == request.user:
            return Response(
                {'detail': 'Вы не можете подписаться на самого себя.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if Follow.objects.filter(
            user=request.user,
            following=user_to_follow
        ).exists():
            return Response(
                {'detail': 'Вы уже подписаны на этого пользователя.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        Follow.objects.create(user=request.user, following=user_to_follow)
        serializer = self.get_follow_serializer(user_to_follow)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, pk=None):
        user_to_follow = get_object_or_404(User, pk=pk)
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
