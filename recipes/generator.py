# recipes/generator.py
import random
from decimal import Decimal
from .utils import calculate_recipe_nutrition

IDEAL_MEAL_DISTRIBUTION = {
    'BREAKFAST': Decimal('0.30'),
    'LUNCH': Decimal('0.40'),
    'DINNER': Decimal('0.30'),
}

def find_best_meal_plan(possible_recipes, target_calories, nutrition_targets):
    """
    Подбирает наилучший план питания из возможных рецептов.
    Использует случайный поиск с итерациями для нахождения оптимальной комбинации.
    """

    target_calories_decimal = Decimal(target_calories)
    
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
        ideal_breakfast_calories = target_calories_decimal * IDEAL_MEAL_DISTRIBUTION['BREAKFAST']
        ideal_lunch_calories = target_calories_decimal * IDEAL_MEAL_DISTRIBUTION['LUNCH']
        ideal_dinner_calories = target_calories_decimal * IDEAL_MEAL_DISTRIBUTION['DINNER']

        # 5.2. Считаем отклонения для каждого приема пищи
        breakfast_deviation = (b_choice['nutrition']['calories_per_serving'] - ideal_breakfast_calories) ** 2
        lunch_deviation = (l_choice['nutrition']['calories_per_serving'] - ideal_lunch_calories) ** 2
        dinner_deviation = (d_choice['nutrition']['calories_per_serving'] - ideal_dinner_calories) ** 2

        # 5.3. Считаем отклонение по общей калорийности (остается главным)
        total_calories_deviation = (current_calories - target_calories_decimal) ** 2

        # 5.4. Складываем все штрафы вместе. 
        # Мы можем дать разный "вес" каждому штрафу. Штраф за общую калорийность важнее,
        # поэтому его коэффициент будет выше.
        # Например, вес 1.0 для общего, и 0.5 для каждого приема пищи.
        score = (total_calories_deviation * Decimal('1.0')) + \
        (breakfast_deviation * Decimal('0.5')) + \
        (lunch_deviation * Decimal('0.5')) + \
        (dinner_deviation * Decimal('0.5'))
        
        if score < best_score:
            best_score = score
            best_combination = {
                'breakfast': b_choice,
                'lunch': l_choice,
                'dinner': d_choice,
            }

    # Проверка на адекватность лучшей найденной комбинации
    if best_combination:
        final_calories = best_combination['breakfast']['nutrition']['calories_per_serving'] + \
                         best_combination['lunch']['nutrition']['calories_per_serving'] + \
                         best_combination['dinner']['nutrition']['calories_per_serving']
        
        # Считаем отклонение от цели в процентах
        deviation_percent = abs(final_calories - target_calories_decimal) / target_calories_decimal
        
        # Если отклонение больше порога 15%, то результат неадекватный
        if deviation_percent > 0.15: 
            return None
    
    # Возвращает лучшую найденную комбинацию (может быть None)
    return best_combination