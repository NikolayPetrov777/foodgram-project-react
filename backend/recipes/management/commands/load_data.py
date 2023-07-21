import json
import os

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):

    help = 'Загрузка ингредиентов'

    path = os.path.abspath('data/ingredients.json')

    def handle(self, *args, **kwargs):
        with open(self.path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        for note in data:
            try:
                Ingredient.objects.get_or_create(**note)
                print(f'{note["name"]} уже загружен')
            except Exception as error:
                print(f'Ошибка при загрузке {note["name"]} в базу.\n'
                      f'Ошибка: {error}')

        print('Загрузка завершена успешно!')
