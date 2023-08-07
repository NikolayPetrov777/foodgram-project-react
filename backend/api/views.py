from django.db.models import Exists, OuterRef, Value
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.conf import settings
from djoser.views import UserViewSet
from rest_framework import permissions, status, viewsets
from rest_framework.filters import SearchFilter
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipeFilter
from api.permissions import IsAuthor
from api.serializers import (CustomUserSerializer, FavoriteSerializer,
                             FollowSerializer, IngredientSerializer,
                             RecipeSerializer, RecipeWriteSerializer,
                             ShoppingCardSerializer, TagSerializer)
from api.viewsets import ListRetriveViewSet, ListViewSet
from recipes.models import (Favorite, Follow, Ingredient, Recipe,
                            ShoppingList, Tag)
from users.models import User


class IngredientViewSet(ListRetriveViewSet):
    """Ингредиенты."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filterset_class = IngredientFilter


class TagViewSet(ListRetriveViewSet):
    """Теги."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """Рецепты."""

    filter_backends = (DjangoFilterBackend, )
    filterset_class = RecipeFilter
    ordering = ('-pub_date',)

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return Recipe.objects.annotate(
                is_favorited=Exists(
                    Favorite.objects.filter(user=user, recipe=OuterRef('pk'))
                ),
                is_in_shopping_cart=Exists(
                    ShoppingList.objects.filter(user=user,
                                                recipe=OuterRef('pk'))
                )
            ).all()
        return Recipe.objects.annotate(
            is_favorited=Value(False),
            is_in_shopping_cart=Value(False)
        ).all()

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeSerializer
        return RecipeWriteSerializer

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return (permissions.AllowAny(),)
        return (permissions.IsAuthenticated(), IsAuthor(),)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class ListSubscribeViewSet(ListViewSet):
    """Список подписок пользователя."""

    serializer_class = FollowSerializer
    permission_classes = (IsAuthenticated,)
    ordering = ('id',)

    def get_queryset(self):
        user = self.request.user
        return user.follower.all()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class CustomUserViewSet(UserViewSet):
    """Пользователи."""

    serializer_class = CustomUserSerializer
    queryset = User.objects.all()
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_serializer_class(self):
        if self.action == 'create':
            if settings.USER_CREATE_PASSWORD_RETYPE:
                return settings.SERIALIZERS.user_create_password_retype
            return settings.SERIALIZERS.user_create
        if self.action == 'set_password':
            if settings.SET_PASSWORD_RETYPE:
                return settings.SERIALIZERS.set_password_retype
            return settings.SERIALIZERS.set_password
        return self.serializer_class

    @action(['get'], detail=False)
    def me(self, request, *args, **kwargs):
        self.get_object = self.get_instance
        return self.retrieve(request, *args, **kwargs)


def add_object(request, model_serializer, recipe_id):
    """Метод создания объектов."""

    serializer = model_serializer(data=request.data,
                                  context={'request': request,
                                  'recipe_id': recipe_id})
    serializer.is_valid(raise_exception=True)
    serializer.save(user=request.user,
                    recipe=get_object_or_404(Recipe, id=recipe_id))
    return Response(serializer.data, status=status.HTTP_201_CREATED)


def del_object(request, model, recipe_id):
    """Метод удаления объектов."""

    model.objects.get(
        user=request.user,
        recipe=get_object_or_404(Recipe, id=recipe_id)
    ).delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['DELETE', 'POST'])
@permission_classes([IsAuthenticated])
def add_del_subscribe(request, user_id):
    """Добавить/удалить подписку."""

    try:
        author = User.objects.get(id=user_id)
    except Exception: 
        return Response(status=status.HTTP_404_NOT_FOUND)
    if request.method == 'POST':
        serializer = FollowSerializer(
            data=request.data,
            context={'request': request, 'user_id': user_id}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user, author=author)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    serializer = FollowSerializer(
        data=request.data,
        context={'request': request, 'user_id': user_id}
    )
    serializer.is_valid(raise_exception=True)
    Follow.objects.filter(
        user=request.user,
        author=author
    ).delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def add_del_shopping_cart(request, recipe_id):
    """Добавить/удалить список покупок."""

    if request.method == 'POST':
        return add_object(request, ShoppingCardSerializer, recipe_id)
    return del_object(request, ShoppingList, recipe_id)


@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def favorite_view(request, recipe_id):
    """Добавить/удалить из избранного."""

    if request.method == 'POST':
        return add_object(request, FavoriteSerializer, recipe_id)
    return del_object(request, Favorite, recipe_id)
