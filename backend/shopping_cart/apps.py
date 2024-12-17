from django.apps import AppConfig


class ShoppingCartConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shopping_cart'
    verbose_name = 'Список покупок'
    verbose_name_plural = 'Списки покупок'
