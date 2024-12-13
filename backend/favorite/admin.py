from django.contrib import admin

from .models import Favorite


@admin.register(Favorite)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'recipe',
    )
    list_filter = (
        'user',
    )
    search_fields = (
        'user',
    )
