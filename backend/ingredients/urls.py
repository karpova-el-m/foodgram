from django.urls import include, path
from rest_framework import routers

from .views import IngredientViewSet

app_name = 'ingredients'

router = routers.DefaultRouter()
router.register(r'ingredients', IngredientViewSet, basename='ingredients')

urlpatterns = [
    path('', include(router.urls)),
]
