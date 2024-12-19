import os

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.utils.html import mark_safe
from django.conf import settings

User = get_user_model()

DEFAULT_AVATAR_PATH = os.path.join(
    settings.BASE_DIR,
    'images',
    'defolt_avatar.jpg'
)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        'id',
        'username',
        'email',
        'first_name',
        'last_name',
        'avatar_preview',
        'is_staff',
        'is_superuser',
    )
    search_fields = (
        'username',
        'email',
        'first_name',
        'last_name',
    )
    list_filter = (
        'is_staff',
        'is_superuser',
    )
    ordering = ('id',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Информация', {'fields': ('first_name', 'last_name', 'avatar')}),
        ('Права доступа', {'fields': (
            'is_active',
            'is_staff',
            'is_superuser',
            'groups',
            'user_permissions'
        )}),
    )
    add_fieldsets = ((None, {
        'classes': ('wide',),
        'fields': (
            'email',
            'username',
            'password1',
            'password2',
            'first_name',
            'last_name',
            'avatar',
            'is_staff',
            'is_active'
        )}),
    )

    @admin.display(description='Аватар')
    def avatar_preview(self, obj):
        if obj.avatar:
            return mark_safe(
                f'<img src="{obj.avatar.url}" width="50" height="50" />'
            )
        return mark_safe(
            '<img src="/images/default_avatar.jpg" width="50" height="50" '
            'style="border-radius: 50%;" />'
        )
