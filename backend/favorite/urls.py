from django.urls import include, path
from rest_framework import routers

from .views import FavoriteViewSet

app_name = 'favorite'

router = routers.DefaultRouter()
router.register(r'recipes', FavoriteViewSet, basename='favorite')

urlpatterns = [
    path('', include(router.urls)),
]
