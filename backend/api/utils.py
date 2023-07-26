from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from recipes.models import IngredientInRecipe


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_shopping_cart(request):
    """Скачать список покупок."""
    ingredients = IngredientInRecipe.objects.filter(
        recipe__recipe_to_shopping__user=request.user
    )
    shopping_data = {}
    for ingredient in ingredients:
        if str(ingredient.ingredient) in shopping_data:
            shopping_data[f'{str(ingredient.ingredient)}'] += ingredient.amount
        else:
            shopping_data[f'{str(ingredient.ingredient)}'] = ingredient.amount
    filename = 'shopping-list.txt'
    content = ''
    for ingredient, amount in shopping_data.items():
        content += f"{ingredient} - {amount};\n\n"
    response = HttpResponse(content, content_type='text/plain',
                            status=status.HTTP_200_OK)
    response['Content-Disposition'] = 'attachment; filename={0}'.format(
        filename)
    return response
