from rest_framework import serializers

from recipes.models import RecipeIngredient

from .models import Ingredient


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор объекта ингредиент."""
    amount = serializers.SerializerMethodField()

    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measurement_unit', 'amount']

    def get_amount(self, obj):
        recipe_id = self.context.get('recipe_id')
        if recipe_id:
            recipe_ingredient = RecipeIngredient.objects.filter(
                recipe_id=recipe_id, ingredient=obj
            ).first()
            if recipe_ingredient:
                amount = recipe_ingredient.amount
                return amount

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if not self.context.get('recipe_id'):
            representation.pop('amount', None)
        return representation
