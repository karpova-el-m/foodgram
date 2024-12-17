from django.apps import AppConfig


class IngredientsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ingredients'
    verbose_name = 'Ингредиент'
    verbose_name_plural = 'Ингредиенты'
