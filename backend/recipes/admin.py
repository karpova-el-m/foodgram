from django.contrib import admin

from .models import Recipe, RecipeIngredient


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'author',
    )
    list_filter = (
        'tags',
    )
    search_fields = (
        'name',
        'author',
    )
    inlines = [RecipeIngredientInline]
    filter_horizontal = (
        'tags',
    )
