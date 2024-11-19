from rest_framework import serializers

from recipes.models import Recipe, Ingredient, Tag, RecipeIngredient


class IngredientSerializer(serializers.ModelSerializer):
    amount = serializers.SerializerMethodField()

    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measurement_unit', 'amount']

    def get_amount(self, obj):
        recipe_id = self.context.get('recipe_id')
        if recipe_id:
            recipe_ingredient = RecipeIngredient.objects.filter(recipe_id=recipe_id, ingredient=obj).first()
            if recipe_ingredient:
                return recipe_ingredient.amount
        return None


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = serializers.SerializerMethodField()
    author = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username'
    )
    tags = TagSerializer(read_only=True, many=True)

    class Meta:
        model = Recipe
        fields = [
            'id',
            'author',
            'name',
            'text',
            'cooking_time',
            'image',
            'tags',
            'ingredients'
        ]

    def get_ingredients(self, obj):
        ingredients = obj.ingredients.all()
        serializer = IngredientSerializer(ingredients, many=True, context={'recipe_id': obj.id})
        return serializer.data
