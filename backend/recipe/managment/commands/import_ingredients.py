import csv

from django.core.management.base import BaseCommand

from recipe.models import Ingredient


class Command(BaseCommand):
    help = 'Импорт ингредиентов из CSV-файла'

    def add_arguments(self, parser):
        parser.add_argument('csv_path', type=str, help='Путь к CSV-файлу')

    def handle(self, *args, **options):
        csv_path = options['csv_path']
        with open(csv_path, encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if len(row) < 2:
                    self.stdout.write(
                        self.style.WARNING(f'Пропущена строка: {row}')
                    )
                    continue
                name, measurement_unit = row[0], row[1]
                Ingredient.objects.get_or_create(
                    name=name,
                    measurement_unit=measurement_unit
                )
        self.stdout.write(self.style.SUCCESS('Импорт ингредиентов завершён!'))
