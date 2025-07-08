# recipes/generator.py
import random
from .utils import calculate_recipe_nutrition

def find_best_meal_plan(possible_recipes, target_calories, nutrition_targets):
    """
    Подбирает наилучший план питания из возможных рецептов.
    Использует случайный поиск с итерациями для нахождения оптимальной комбинации.
    """
    
    breakfasts = []
    lunches = []
    dinners = []

    for recipe in possible_recipes:
        nutrition_info = calculate_recipe_nutrition(recipe)
        recipe_data = {'recipe': recipe, 'nutrition': nutrition_info}
        
        if recipe.meal_type == 'BREAKFAST':
            breakfasts.append(recipe_data)
        elif recipe.meal_type == 'LUNCH':
            lunches.append(recipe_data)
        elif recipe.meal_type == 'DINNER':
            dinners.append(recipe_data)

    if not breakfasts or not lunches or not dinners:
        return None

    best_combination = None
    # Начальный "штраф"
    best_score = float('inf') 
    
    number_of_attempts = 500
    for _ in range(number_of_attempts):
        b_choice = random.choice(breakfasts)
        l_choice = random.choice(lunches)
        d_choice = random.choice(dinners)

        # Считаем суммарный КБЖУ для комбинации
        current_calories = b_choice['nutrition']['calories_per_serving'] + \
                           l_choice['nutrition']['calories_per_serving'] + \
                           d_choice['nutrition']['calories_per_serving']
        
        current_proteins = b_choice['nutrition']['proteins_per_serving'] + \
                           l_choice['nutrition']['proteins_per_serving'] + \
                           d_choice['nutrition']['proteins_per_serving']
        
        current_fats = b_choice['nutrition']['fats_per_serving'] + \
                     l_choice['nutrition']['fats_per_serving'] + \
                     d_choice['nutrition']['fats_per_serving']

        current_carbs = b_choice['nutrition']['carbs_per_serving'] + \
                      l_choice['nutrition']['carbs_per_serving'] + \
                      d_choice['nutrition']['carbs_per_serving']

        # Проверяет комбинацию на соответствие жестким ограничениям
        if current_proteins < nutrition_targets['proteins']:
            continue
        
        if current_fats < nutrition_targets['fats']:
            continue

        if nutrition_targets['carb_constraint_type'] == 'AT_MOST' and current_carbs > nutrition_targets['carbs']:
            continue
        if nutrition_targets['carb_constraint_type'] == 'AT_LEAST' and current_carbs < nutrition_targets['carbs']:
            continue

        # Если комбинация валидна, считаем ее "штраф"
        # Чем ближе к цели по калориям, тем лучше.
        score = (current_calories - target_calories) ** 2
        
        if score < best_score:
            best_score = score
            best_combination = {
                'breakfast': b_choice,
                'lunch': l_choice,
                'dinner': d_choice,
            }
    
    # Возвращает лучшую найденную комбинацию (может быть None)
    return best_combination