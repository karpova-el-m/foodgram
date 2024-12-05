from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models
from foodgram_project.constants import (MAX_LENGTH,
                                        MAX_LENGTH_FIRST_AND_LAST_NAME,
                                        MAX_LENGTH_USERNAME, MAX_TITLE_LENGTH,
                                        MEASUREMENT_UNIT_CHOICES)

from .validators import validate_amount, validate_username


class User(AbstractUser):
    """Модель User."""
    email = models.EmailField(unique=True,)
    username = models.CharField(
        max_length=MAX_LENGTH_USERNAME,
        validators=[validate_username],
        unique=True,
    )
    first_name = models.CharField(
        max_length=MAX_LENGTH_FIRST_AND_LAST_NAME,
    )
    last_name = models.CharField(
        max_length=MAX_LENGTH_FIRST_AND_LAST_NAME,
    )
    avatar = models.ImageField(
        upload_to='users/images/',
        null=True,
        blank=True,
        default=None
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']


class Tag(models.Model):
    """Модель Tag."""
    name = models.CharField(
        verbose_name='Тег',
        unique=True,
        max_length=MAX_LENGTH
    )
    slug = models.SlugField(
        unique=True,
        verbose_name='Идентификатор',
        help_text=(
            'Идентификатор страницы для URL; '
            'разрешены символы латиницы, цифры, дефис и подчеркивание.'
        ),
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель Ingredient."""
    name = models.CharField(
        verbose_name='Название ингредиента',
        unique=True,
        max_length=MAX_LENGTH
    )
    measurement_unit = models.CharField(
        max_length=10,
        choices=MEASUREMENT_UNIT_CHOICES,
        verbose_name='Единица измерения'
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


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


class Favorite(models.Model):
    """Модель для рецептов, добавленных в избранное."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Избранное'
    )

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_favorite_combination'
            )
        ]

    def __str__(self):
        return f'{self.user.username} добавил в избранное {self.recipe.name}'
