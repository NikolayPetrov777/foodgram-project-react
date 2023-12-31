from django.urls import include, path
from rest_framework import routers

from api.utils import download_shopping_cart
from api.views import (CustomUserViewSet, IngredientViewSet,
                       ListSubscribeViewSet, RecipeViewSet,
                       TagViewSet, add_del_shopping_cart,
                       add_del_subscribe, favorite_view)

router_v1 = routers.DefaultRouter()

router_v1.register('ingredients', IngredientViewSet,
                   basename='ingredients')
router_v1.register('tags', TagViewSet, basename='tags')
router_v1.register('users/subscriptions', ListSubscribeViewSet,
                   basename='get_subscribe')
router_v1.register('users', CustomUserViewSet)
router_v1.register('recipes', RecipeViewSet, basename='recipes')

function_urls = [
    path('recipes/download_shopping_cart/', download_shopping_cart,
         name='download_shopping_cart'),
    path('recipes/<int:recipe_id>/shopping_cart/', add_del_shopping_cart,
         name='add_del_shopping_cart'),
    path('recipes/<int:recipe_id>/favorite/', favorite_view, name='favorite'),
    path('users/<int:user_id>/subscribe/', add_del_subscribe, name='subscribe')
]


urlpatterns = [
    path('', include(function_urls)),
    path('', include(router_v1.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
