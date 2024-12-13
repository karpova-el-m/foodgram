from django.urls import include, path
from rest_framework import routers

from .views import RecipeViewSet

app_name = 'recipes'

router_v1 = routers.DefaultRouter()
router_v1.register(r'recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path('', include(router_v1.urls)),
]
