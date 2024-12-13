from django.urls import include, path
from rest_framework_nested.routers import NestedSimpleRouter
from rest_framework import routers

from .views import ShoppingCartViewSet

app_name = 'shopping_cart'

router_v1 = routers.DefaultRouter()
router_v1.register(r'recipes', ShoppingCartViewSet, basename='shopping_cart')

urlpatterns = [
    path('', include(router_v1.urls)),
]
