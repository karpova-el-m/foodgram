from django.urls import include, path
from rest_framework import routers

from .views import FavoriteViewSet

app_name = 'favorite'

router_v1 = routers.DefaultRouter()
router_v1.register(r'recipes', FavoriteViewSet, basename='favorite')

urlpatterns = [
    path('', include(router_v1.urls)),
]
