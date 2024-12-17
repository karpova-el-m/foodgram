from django.urls import include, path
from rest_framework import routers

from .views import ShoppingCartViewSet

app_name = 'shopping_cart'

router = routers.DefaultRouter()
router.register(r'recipes', ShoppingCartViewSet, basename='shopping_cart')

urlpatterns = [
    path('', include(router.urls)),
]
