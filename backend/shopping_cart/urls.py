from django.urls import path

from .views import ShoppingCartView

app_name = 'shopping_cart'

urlpatterns = [
    path(
        'recipes/<int:pk>/shopping_cart/',
        ShoppingCartView.as_view(),
        name='add_to_shopping_cart'
    ),
    path(
        'recipes/<int:pk>/shopping_cart/remove/',
        ShoppingCartView.as_view(),
        name='remove_from_shopping_cart'
    ),
]
