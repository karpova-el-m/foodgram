from django.contrib import admin
from django.utils.html import mark_safe
from django.core.exceptions import ValidationError

from .models import Recipe, RecipeIngredient


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        if not obj.ingredients.exists():
            raise ValidationError("Нельзя создать рецепт без ингредиентов.")
        super().save_model(request, obj, form, change)
    list_display = (
        'id',
        'name',
        'author',
        'get_recipe_image',
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

    @admin.display(description='Изображение рецепта')
    def get_recipe_image(self, obj):
        if obj.image:
            return mark_safe(
                f'<img src="{obj.image.url}" width="50" height="50" />'
            )
        return None
