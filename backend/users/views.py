from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from core.mixins import UpdateModelMixin
from core.paginators import CustomPagination
from core.permissions import IsAuthorOrReadOnly
from following.serializers import FollowSerializer, FollowCreateSerializer
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

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'create'):
            return (AllowAny(),)
        return (IsAuthenticated(),)

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
        serializer = self.get_serializer(request.user)
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
        serializer = FollowCreateSerializer(
            data={'following': get_object_or_404(User, pk=pk).id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            serializer.to_representation(serializer.instance),
            status=status.HTTP_201_CREATED
        )

    @subscribe.mapping.delete
    def unsubscribe(self, request, pk=None):
        follow = request.user.following.filter(
            following=get_object_or_404(User, pk=pk)
        )
        if not follow.exists():
            return Response(
                {'detail': 'Вы не подписаны на этого пользователя.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        follow.delete()
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
        subscriptions = request.user.following.all()
        followed_users = [follow.following for follow in subscriptions]
        page = self.paginate_queryset(followed_users)
        serializer = FollowSerializer(
            page if page is not None else followed_users,
            many=True,
            context={'request': request}
        )
        return (
            self.get_paginated_response(serializer.data) if page is not None
            else Response(serializer.data, status=status.HTTP_200_OK)
        )
