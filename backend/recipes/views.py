from django.conf import settings
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from core.filters import RecipeFilter
from core.paginators import CustomPagination
from core.permissions import IsAuthorOrReadOnly
from .models import Recipe
from .serializers import RecipeCreateUpdateSerializer, RecipeSerializer

User = get_user_model()


class RecipeViewSet(ModelViewSet):
    """Вьюсет для модели Recipe."""
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [AllowAny]
    http_method_names = ('get', 'post', 'patch', 'delete')
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = CustomPagination

    def get_permissions(self):
        if self.action in ['destroy', 'partial_update']:
            return [IsAuthorOrReadOnly()]
        elif self.action in ['create']:
            return [IsAuthenticated()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action in ['create', 'partial_update']:
            return RecipeCreateUpdateSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link'
    )
    def get_short_link(self, request, pk=None):
        base_url = getattr(settings, 'BASE_URL')
        short_link = f'{base_url}/{pk}/'
        return Response(
            {'short-link': short_link},
            status=status.HTTP_200_OK
        )
