import base64

from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.fields import CurrentUserDefault
from djoser.serializers import UserSerializer

from recipes.models import (Favorite, Follow, Ingredient, IngredientInRecipe,
                            Recipe, ShoppingList, Tag)
from users.models import User


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов."""

    class Meta:
        fields = (
            'id',
            'name',
            'measurement_unit'
        )
        model = Ingredient


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тегов."""

    class Meta:
        fields = (
            'id',
            'name',
            'color',
            'slug'
        )
        model = Tag


class RecipeShortSerializer(serializers.ModelSerializer):
    """Упрощённый сериализатор рецепта."""

    id = serializers.ReadOnlyField()
    name = serializers.ReadOnlyField()
    image = serializers.ImageField(read_only=True)
    cooking_time = serializers.ReadOnlyField()

    class Meta:
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )
        model = Recipe


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов в рецепте для чтения."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount'
        )
        model = IngredientInRecipe


class IngredientInRecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов в рецепте для записи."""

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all(),
                                            source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount'
        )
        model = IngredientInRecipe


class CustomUserSerializer(UserSerializer):
    """Сериализатор пользователя."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )
        model = User

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        return user.is_authenticated and user.follower.filter(
            author=obj).exists()


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор рецепта."""

    is_favorited = serializers.BooleanField(read_only=True)
    is_in_shopping_cart = serializers.BooleanField(read_only=True)
    tags = TagSerializer(many=True)
    author = CustomUserSerializer()
    ingredients = IngredientInRecipeSerializer(source='ingredientinrecipe_set',
                                               many=True, read_only=True)

    class Meta:
        exclude = ('pub_date',)
        model = Recipe


def func_validate(self, model):
    if (self.context['request'].method == 'POST'
                and model.objects.filter(
                    user=self.context['request'].user,
                    recipe_id=self.context['recipe_id']
        ).exists()):
            raise serializers.ValidationError(
                'Уже добавлено!'
            )
    if (self.context['request'].method == 'DELETE' and not
        model.objects.filter(
            user=self.context['request'].user,
            recipe_id=self.context['recipe_id']
        ).exists()):
            raise serializers.ValidationError(
                'Этот рецепт не в избранном.'
            )


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор избранного."""

    id = serializers.ReadOnlyField(source='recipe.id')
    name = serializers.ReadOnlyField(source='recipe.name')
    image = serializers.ImageField(source='recipe.image', read_only=True)
    cooking_time = serializers.ReadOnlyField(source='recipe.cooking_time')

    class Meta:
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )
        model = Favorite

    def validate(self, data):
        func_validate(self, Favorite)
        return data


class FollowSerializer(serializers.ModelSerializer):
    """Сериализатор подписок."""

    email = serializers.ReadOnlyField(source='author.email')
    id = serializers.ReadOnlyField(source='author.id')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )
        model = Follow

    def validate(self, data):
        if self.context['request'].method == 'POST' and Follow.objects.filter(
                user=self.context['request'].user,
                author_id=self.context['user_id']
        ).exists():
            raise serializers.ValidationError(
                'Такая подписка уже есть!'
            )
        if (self.context['request'].method == 'POST'
                and self.context['request'].user.id
                == self.context['user_id']):
            raise serializers.ValidationError(
                'На себя нельзя подписаться!'
            )
        if (self.context['request'].method == 'DELETE' and not
            Follow.objects.filter(
                user=self.context['request'].user,
                author_id=self.context['user_id']
        ).exists()):
            raise serializers.ValidationError(
                'Такой подписки нет!'
            )
        return data

    def get_recipes(self, obj):
        recipes_limit = self.context['request'].query_params.get(
            'recipes_limit'
        )
        queryset = obj.author.recipes.all()
        if recipes_limit:
            queryset = queryset[:int(recipes_limit)]
        serializer = RecipeShortSerializer(queryset, many=True)
        return serializer.data

    def get_is_subscribed(self, obj):
        return Follow.objects.filter(user=self.context['request'].user,
                                     author=obj.author).exists()

    def get_recipes_count(self, obj):
        return obj.author.recipes.count()


class Base64ImageField(serializers.ImageField):
    """Сериализатор поля изображения."""
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class ShoppingCardSerializer(serializers.ModelSerializer):
    """Сериализатор списка покупок."""

    id = serializers.ReadOnlyField(source='recipe.id')
    name = serializers.ReadOnlyField(source='recipe.name')
    image = serializers.ImageField(source='recipe.image', read_only=True)
    cooking_time = serializers.ReadOnlyField(source='recipe.cooking_time')

    class Meta:
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )
        model = ShoppingList

    def validate(self, data):
        func_validate(self, ShoppingList)
        return data


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор рецепта для записи."""

    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    author = CustomUserSerializer(
        read_only=True, default=CurrentUserDefault())
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )
    image = Base64ImageField()
    ingredients = IngredientInRecipeWriteSerializer(
        many=True,
        source='ingredientinrecipe_set',
    )

    class Meta:
        exclude = ('pub_date',)
        read_only_fields = ('author',)
        model = Recipe

    def validate(self, data):
        tags = self.initial_data.get('tags')
        if not tags:
            raise serializers.ValidationError(
                'Не указаны теги.'
            )
        ingredients = self.initial_data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                'Не указаны ингредиенты.'
            )
        ingredients = []
        for ingredient in self.context['request'].data['ingredients']:
            if ingredient in ingredients:
                raise serializers.ValidationError(
                    'Ингредиенты не должны повторяться.'
                )
            if int(ingredient['amount']) <= 0:
                raise serializers.ValidationError(
                    'Вес должен быть больше нуля.'
                )
            ingredients.append(ingredient)
        cooking_time = data.get('cooking_time')
        if cooking_time <= 0:
            raise serializers.ValidationError(
                'Время готовки должно быть больше нуля.'
            )
        return data

    def get_is_favorited(self, obj):
        return Favorite.objects.filter(user=self.context['request'].user,
                                       recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        return ShoppingList.objects.filter(user=self.context['request'].user,
                                           recipe=obj).exists()

    def to_representation(self, instance):
        serializer = RecipeSerializer(
            instance,
            context={'request': self.context.get('request')}
        )
        return serializer.data


    def create_ingredients(self, ingredients, recipe):
        data = []
        for ingredient in ingredients:
            data.append(IngredientInRecipe(
                recipe=recipe,
                ingredient=ingredient['ingredient']['id'],
                amount=ingredient['amount']
            ))
        IngredientInRecipe.objects.bulk_create(data)
    
    def create(self, validated_data):
        ingredients = validated_data.pop('ingredientinrecipe_set')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        self.create_ingredients(ingredients, recipe)
        recipe.tags.set(tags)
        return recipe

    def update(self, instance, validated_data):
        instance.image = validated_data.get('image', instance.image)
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        ingredients = validated_data.pop('ingredientinrecipe_set')
        tags = validated_data.pop('tags')
        instance.tags.set(tags)
        instance.ingredients.set([])
        instance.save()
        self.create_ingredients(ingredients, instance)
        return super().update(instance, validated_data)
