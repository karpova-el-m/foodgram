from django.contrib import admin
from .models import ShoppingList


@admin.register(ShoppingList)
class ShoppingListAdmin(admin.ModelAdmin):
    list_display = ('id', 'user')
    search_fields = (
        'user__username',
        'user__email'
    )
    list_filter = (
        'user',
    )
    ordering = (
        'user__id',
    )
