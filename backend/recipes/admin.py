from django.contrib import admin
from django.db.models import Count, OuterRef

from recipes.models import (Favorite, Follow, Ingredient, IngredientInRecipe,
                            Recipe, ShoppingList, Tag)


class TagsInline(admin.TabularInline):
    """Редактирование тегов в рецепте."""

    model = Recipe.tags.through
    extra = 3


class IngredientsInline(admin.TabularInline):
    """Редактирование ингредиентов в рецепте."""

    model = Recipe.ingredients.through
    extra = 3
    min_num = 1


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Панель администратора для ингредиентов."""

    list_display = (
        'name',
        'measurement_unit'
    )
    list_filter = ('name',)
    list_per_page = 50
    search_fields = ('name',)
    search_help_text = ('Поиск по названию',)
    actions_on_bottom = True


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Панель администратора для тегов."""

    list_display = (
        'id',
        'name',
        'color',
        'slug'
    )
    list_filter = ('name',)
    list_editable = ('color',)
    prepopulated_fields = {
        'slug': ('name',)
    }
    list_per_page = 50
    search_fields = ('name',)
    search_help_text = ('Поиск по имени тега',)
    actions_on_bottom = True


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Панель администратора для рецептов."""

    list_display = (
        'id',
        'name',
        'author',
        'favorite_count'
    )
    inlines = (
        TagsInline,
        IngredientsInline,
    )
    fields = (
        'name',
        'author',
        'image',
        'text',
        'cooking_time',
        'tags',
        'favorite_count'
    )
    search_fields = ('name', 'author__username', 'tags__name')
    readonly_fields = ('favorite_count',)
    list_filter = (
        'author',
        'name',
        'tags'
    )

    def get_queryset(self, request):
        return Recipe.objects.annotate(
            favorite_count=Count(
                Favorite.objects.filter(recipe=OuterRef('pk')).values('id')
            )
        )

    @admin.display(
        ordering='favorite_count',
        description='Сколько раз добавили в избранное',
    )
    def favorite_count(self, obj):
        return obj.favorite_count


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    """Панель администратора для подписок."""

    list_display = (
        'user',
        'author'
    )


@admin.register(IngredientInRecipe)
class IngredientInRecipeAdmin(admin.ModelAdmin):
    """Панель администратора для ингредиентов в рецептах."""

    list_display = (
        'recipe',
        'ingredient',
        'amount'
    )


@admin.register(ShoppingList)
class ShoppingListAdmin(admin.ModelAdmin):
    """Панель администратора для списка покупок."""

    list_display = (
        'recipe',
        'user'
    )
