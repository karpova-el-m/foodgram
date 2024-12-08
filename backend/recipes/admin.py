from django.contrib import admin
from django.contrib.auth import get_user_model

from .models import Ingredient, Recipe, RecipeIngredient, Tag

User = get_user_model()


@admin.register(User)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'username',
        'email',
        'first_name',
        'last_name'
    )
    search_fields = (
        'username',
        'email',
        'first_name',
        'last_name'
    )
    list_filter = (
        'is_staff',
        'is_superuser'
    )
    ordering = (
        'id',
    )


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'measurement_unit'
    )
    list_editable = (
        'measurement_unit',
    )
    search_fields = (
        'name',
    )
    list_filter = (
        'measurement_unit',
    )


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


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'slug'
    )
    search_fields = (
        'name',
    )
