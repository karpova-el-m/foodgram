from django.contrib import admin
from django.utils.html import mark_safe
from django.core.exceptions import ValidationError
from django import forms

from .models import Recipe, RecipeIngredient


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


class RecipeAdminForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        ingredients = cleaned_data.get('ingredients')
        if not ingredients or not ingredients.exists():
            raise ValidationError('Нельзя создать рецепт без ингредиентов.')
        return cleaned_data


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    form = RecipeAdminForm
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
