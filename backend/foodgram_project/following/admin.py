from django.contrib import admin

from .models import Follow


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'following')
    search_fields = (
        'user__username',
        'user__email',
        'following__username',
        'following__email'
    )
    list_filter = (
        'user',
        'following'
    )
    ordering = (
        'id',
    )
