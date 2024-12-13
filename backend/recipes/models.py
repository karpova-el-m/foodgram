from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

from core.constants import MAX_LENGTH, MAX_TITLE_LENGTH
from core.validators import validate_amount
from ingredients.models import Ingredient
from tags.models import Tag

User = get_user_model()


class Recipe(models.Model):
    """Модель Recipe."""
    name = models.CharField(
        max_length=MAX_TITLE_LENGTH,
        verbose_name='Название'
    )
    text = models.TextField(verbose_name='Описание рецепта')
    author = models.ForeignKey(
        User,
        verbose_name='Автор рецепта',
        related_name='recipes',
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создан'
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления, мин.',
        validators=[MinValueValidator(1)]
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        default=None
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты'
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-created_at']

    def __str__(self):
        return self.name[:MAX_LENGTH]


class RecipeIngredient(models.Model):
    """Промежуточная модель RecipeIngredient."""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент'
    )
    amount = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[validate_amount],
        verbose_name='Количество'
    )

    class Meta:
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецепта'

    def __str__(self):
        return f'{self.recipe.name}/{self.ingredient.name}'
