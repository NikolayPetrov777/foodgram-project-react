#  FOODGRAM-PROJECT-REACT

## Что нужно сделать

Настроить запуск сайта, на котором пользователи будут публиковать рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Сервис «Список покупок» позволит пользователям создавать список продуктов, которые нужно купить для приготовления выбранных блюд.

## Запуск проекта через Docker

- Клонировать репозиторий и перейти в него в командной строке:
```yaml
git clone <ссылка с git-hub>
```
- Шаблон наполнения .env расположить по пути infra/.env
```yaml
POSTGRES_USER= # логин для подключения к базе данных
POSTGRES_PASSWORD= # пароль для подключения к БД (установите свой)
POSTGRES_DB= # имя базы данных
DB_HOST=db
DB_PORT= # порт для подключения к БД
```
- Находясь в папке infra/ поднять контейнеры
```yaml
docker-compose up -d --build
```
- Выполнить миграции:
```yaml
docker-compose exec backend python manage.py migrate
```
- Создать суперпользователя:
```yaml
docker-compose exec backend python manage.py migrate
```
- Собрать статику:
```yaml
docker-compose exec backend python manage.py collectstatic --no-input
```
- Наполнить базу заранее заготовленными файлами:
```yaml
docker-compose exec backend python manage.py load_data
```
## Адрес сервера, на котором запущен проект
```yaml
https://piggygram.hopto.org/
```
## Админ-зона
---
Админ-зона: https://piggygram.hopto.org/admin/
```yaml
Логин и пароль суперпользователя для проверки админ-зоны:
Email: nikolaypetroff777@yandex.ru
Username: admin
Password: parol123
```
