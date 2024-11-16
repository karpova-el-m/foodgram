from django.contrib import admin
from .models import Ingredient, Recipe

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)

    def has_module_permission(self, request):
        """Таблица доступна только суперпользователям"""
        return request.user.is_superuser


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'ingredient', 'amount')
    autocomplete_fields = ('ingredient',)
