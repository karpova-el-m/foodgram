# Generated by Django 4.2.16 on 2024-12-17 20:38

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Ingredient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20, unique=True, verbose_name='Название ингредиента')),
                ('measurement_unit', models.CharField(choices=[('г', 'Грамм'), ('кг', 'Килограмм'), ('мг', 'Миллиграмм'), ('л', 'Литр'), ('мл', 'Миллилитр'), ('шт.', 'Штука'), ('ч. л.', 'Чайная ложка'), ('ст. л.', 'Столовая ложка'), ('капля', 'Капля'), ('кусок', 'Кусок'), ('банка', 'Банка'), ('стакан', 'Стакан'), ('щепотка', 'Щепотка'), ('горсть', 'Горсть')], max_length=10, verbose_name='Единица измерения')),
            ],
            options={
                'verbose_name': 'Ингредиент',
                'verbose_name_plural': 'Ингредиенты',
            },
        ),
        migrations.AddConstraint(
            model_name='ingredient',
            constraint=models.UniqueConstraint(fields=('name', 'measurement_unit'), name='unique_ingredient_combination'),
        ),
    ]
