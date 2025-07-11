from decimal import Decimal # Используем Decimal для точных расчетов

def calculate_recipe_nutrition(recipe):
    """
    Рассчитывает пищевую ценность (КБЖУ) для всего рецепта
    и для одной порции на основе его ингредиентов.

    Аргументы:
        recipe (Recipe): объект модели Recipe.

    Возвращает:
        dict: Словарь с рассчитанными значениями КБЖУ.
    """
    total_calories = Decimal(0)
    total_proteins = Decimal(0)
    total_fats = Decimal(0)
    total_carbs = Decimal(0)

    # 1. Проходим по всем ингредиентам в рецепте через связующую модель.
    for item in recipe.recipeingredient_set.all():
        ingredient = item.ingredient
        # Коэффициент для пересчета КБЖУ со 100г на реальный вес в рецепте.
        weight_factor = Decimal(item.weight_grams) / Decimal(100)
        
        total_calories += ingredient.calories * weight_factor
        total_proteins += ingredient.proteins * weight_factor
        total_fats += ingredient.fats * weight_factor
        total_carbs += ingredient.carbs * weight_factor
        
    # 2. Рассчитываем КБЖУ на одну порцию
    servings = Decimal(recipe.servings)
    if servings > 0:
        calories_per_serving = total_calories / servings
        proteins_per_serving = total_proteins / servings
        fats_per_serving = total_fats / servings
        carbs_per_serving = total_carbs / servings
    else:
        # На случай, если в базе у рецепта почему-то 0 порций
        calories_per_serving = proteins_per_serving = fats_per_serving = carbs_per_serving = Decimal(0)
        
    # 3. Возвращает результат с округленными значениями.
    return {
        'total_calories': round(total_calories, 2),
        'calories_per_serving': round(calories_per_serving, 2),
        'proteins_per_serving': round(proteins_per_serving, 2),
        'fats_per_serving': round(fats_per_serving, 2),
        'carbs_per_serving': round(carbs_per_serving, 2),
    }