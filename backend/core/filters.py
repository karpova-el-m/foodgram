from django_filters.rest_framework import BooleanFilter, CharFilter, FilterSet

from ingredients.models import Ingredient
from recipes.models import Recipe


class IngredientFilter(FilterSet):
    """Кастомный фильтр для модели Ingredient."""
    name = CharFilter(method='filter_name')

    class Meta:
        model = Ingredient
        fields = ['name']

    def filter_name(self, queryset, name, value):
        """Кастомный фильтр для поиска по имени ингредиента."""
        if value:
            return queryset.filter(name__icontains=value)
        return queryset


class RecipeFilter(FilterSet):
    """Кастомный фильтр для модели Recipe."""
    tags = CharFilter(method='filter_tags')
    is_favorited = BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = BooleanFilter(method='filter_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ('author',)

    def filter_tags(self, queryset, name, value):
        """Фильтрует рецепты по тегам, переданным в запросе."""
        tags = self.request.query_params.getlist('tags')
        if tags:
            queryset = queryset.filter(
                tags__name__in=tags
            ).distinct() | queryset.filter(
                tags__slug__in=tags
            ).distinct()
        return queryset

    def filter_is_favorited(self, queryset, name, value):
        """Фильтрация по параметру is_favorited."""
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(favorites__user=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """Фильтрация по параметру is_in_shopping_cart."""
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(shopping_cart__user=user)
        return queryset
