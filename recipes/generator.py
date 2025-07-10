# recipes/generator.py (ФИНАЛЬНАЯ ВЕРСИЯ 5.0 - с итерационной подгонкой по дефициту)

import random
from decimal import Decimal
from .utils import calculate_recipe_nutrition

# Идеальные пропорции калорий для каждого приема пищи
IDEAL_MEAL_DISTRIBUTION = {
    'BREAKFAST': Decimal('0.30'),
    'LUNCH': Decimal('0.40'),
    'DINNER': Decimal('0.30'),
}

def find_best_meal_plan(possible_recipes, target_calories, nutrition_targets):
    """
    Подбирает наилучший план питания, используя "умный" старт,
    масштабирование порций и итерационную подгонку.
    """
    
    # 1. Подготовка данных
    all_recipes_with_nutrition = []
    for recipe in possible_recipes:
        nutrition_info = calculate_recipe_nutrition(recipe)
        if nutrition_info['calories_per_serving'] > 0:
            all_recipes_with_nutrition.append({'recipe': recipe, 'nutrition': nutrition_info})
            
    breakfasts = [r for r in all_recipes_with_nutrition if r['recipe'].meal_type == 'BREAKFAST']
    lunches = [r for r in all_recipes_with_nutrition if r['recipe'].meal_type == 'LUNCH']
    dinners = [r for r in all_recipes_with_nutrition if r['recipe'].meal_type == 'DINNER']

    if not breakfasts or not lunches or not dinners:
        return None

    # 2. Инициализация для поиска
    best_combination = None
    best_score = float('inf') 
    target_calories_decimal = Decimal(target_calories)

    # 3. Основной цикл попыток
    number_of_attempts = 300
    for _ in range(number_of_attempts):
        
        # 4. Выбираем случайную базовую комбинацию
        base_plan_data = {
            'breakfast': random.choice(breakfasts),
            'lunch': random.choice(lunches),
            'dinner': random.choice(dinners)
        }
        
        # 5. Инициализируем порции
        servings = {'breakfast': 1, 'lunch': 1, 'dinner': 1}
        
        # 6. Итерационная подгонка порций (до 5 шагов)
        for i in range(5):
            current_calories = sum(base_plan_data[mt]['nutrition']['calories_per_serving'] * s for mt, s in servings.items())

            if abs(current_calories - target_calories_decimal) / target_calories_decimal <= 0.20:
                break
            
            if current_calories < target_calories_decimal:
                deficits = {}
                for meal_type, data in base_plan_data.items():
                    ideal_calories = target_calories_decimal * IDEAL_MEAL_DISTRIBUTION[meal_type.upper()]
                    actual_calories = data['nutrition']['calories_per_serving'] * servings[meal_type]
                    deficits[meal_type] = ideal_calories - actual_calories
                
                if any(v > 0 for v in deficits.values()):
                    meal_to_increase = max(deficits, key=deficits.get)
                    servings[meal_to_increase] += 1
            elif current_calories > target_calories_decimal:
                meal_calories = {mt: data['nutrition']['calories_per_serving'] * servings[mt] for mt, data in base_plan_data.items()}
                meal_to_decrease = max(meal_calories, key=meal_calories.get)
                if servings[meal_to_decrease] > 1:
                    servings[meal_to_decrease] -= 1
        
        # 7. Расчет итоговых показателей после подгонки
        total_calories = sum(base_plan_data[mt]['nutrition']['calories_per_serving'] * s for mt, s in servings.items())
        total_proteins = sum(base_plan_data[mt]['nutrition']['proteins_per_serving'] * s for mt, s in servings.items())
        total_fats = sum(base_plan_data[mt]['nutrition']['fats_per_serving'] * s for mt, s in servings.items())
        total_carbs = sum(base_plan_data[mt]['nutrition']['carbs_per_serving'] * s for mt, s in servings.items())

        # 8. Проверка на соответствие жестким порогам БЖУ
        is_valid = True
        if total_proteins < nutrition_targets['proteins'] or total_fats < nutrition_targets['fats']:
            is_valid = False
        if nutrition_targets['carb_constraint_type'] == 'AT_MOST' and total_carbs > nutrition_targets['carbs']:
            is_valid = False
        if nutrition_targets['carb_constraint_type'] == 'AT_LEAST' and total_carbs < nutrition_targets['carbs']:
            is_valid = False
        
        if not is_valid:
            continue

        # 9. Расчет "оценки" (штрафа)
        score = (total_calories - target_calories_decimal) ** 2
        for meal_type, data in base_plan_data.items():
            ideal_meal_calories = target_calories_decimal * IDEAL_MEAL_DISTRIBUTION[meal_type.upper()]
            current_meal_calories = data['nutrition']['calories_per_serving'] * servings[meal_type]
            score += (current_meal_calories - ideal_meal_calories) ** 2 * Decimal('0.3')

        # 10. Сохранение лучшей комбинации
        if score < best_score:
            best_score = score
            best_combination = {
                'breakfast': {'recipe_data': base_plan_data['breakfast'], 'servings': servings['breakfast']},
                'lunch': {'recipe_data': base_plan_data['lunch'], 'servings': servings['lunch']},
                'dinner': {'recipe_data': base_plan_data['dinner'], 'servings': servings['dinner']},
            }

    # 11. Финальная проверка на адекватность
    if best_combination:
        final_calories = sum(v['recipe_data']['nutrition']['calories_per_serving'] * v['servings'] for v in best_combination.values())
        if final_calories > 0:
            deviation_percent = abs(final_calories - target_calories_decimal) / target_calories_decimal
            if deviation_percent > Decimal('0.25'):
                return None
    
    return best_combination