# Generated by Django 5.2.3 on 2025-06-29 15:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recipe', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='favorite',
            options={'default_related_name': 'favorites', 'verbose_name': 'Избранный рецепт', 'verbose_name_plural': 'Избранные рецепты'},
        ),
        migrations.AlterModelOptions(
            name='shoppingcart',
            options={'default_related_name': 'shopping_carts', 'verbose_name': 'Рецепт в корзине', 'verbose_name_plural': 'Рецепты в корзине'},
        ),
    ]
