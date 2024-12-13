from django.urls import include, path
from rest_framework import routers

from .views import IngredientViewSet

app_name = 'ingredients'

router_v1 = routers.DefaultRouter()
router_v1.register(r'ingredients', IngredientViewSet, basename='ingredients')

urlpatterns = [
    path('', include(router_v1.urls)),
]
