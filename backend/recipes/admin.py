from django.contrib import admin
from django.utils.html import mark_safe
from django.db.models import Count

from .models import Recipe, RecipeIngredient


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'author',
        'get_recipe_image',
        'favorite_amount',
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
                f'<img src="{obj.image.url}" width="50" height="50" '
                'style="border-radius: 50%;" />'
            )
        return None

    @admin.display(description='Добавлено в избранное')
    def favorite_amount(self, obj):
        return obj.favorite_amount

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(favorite_amount=Count('favorites'))
