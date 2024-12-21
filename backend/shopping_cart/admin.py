from django.contrib import admin
from django.utils.html import mark_safe

from .models import ShoppingCart


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'recipe',
        'get_recipe_image'
    )
    search_fields = (
        'user__username',
        'user__email',
        'recipe__name',
    )
    list_filter = (
        'user',
        'recipe',
    )
    ordering = ('user__id',)

    @admin.display(description='Изображение рецепта')
    def get_recipe_image(self, obj):
        if obj.recipe.image:
            return mark_safe(
                f'<img src="{obj.recipe.image.url}" width="50" height="50" '
                'style="border-radius: 50%;" />'
            )
        return None
