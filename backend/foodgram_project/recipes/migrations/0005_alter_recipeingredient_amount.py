# Generated by Django 4.2.16 on 2024-11-27 20:50

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0004_favorite_favorite_unique_favorite_combination'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipeingredient',
            name='amount',
            field=models.DecimalField(decimal_places=2, max_digits=6, validators=[django.core.validators.MinValueValidator(1.01)], verbose_name='Количество'),
        ),
    ]
