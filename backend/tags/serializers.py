from rest_framework import serializers

from .models import Tag


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор объекта тег."""
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']
