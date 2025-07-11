import random
from decimal import Decimal
from .utils import calculate_recipe_nutrition

# Задаем "идеальные" пропорции калорий для каждого приема пищи.
# Используется для расчета штрафа за дисбаланс в плане питания.
IDEAL_MEAL_DISTRIBUTION = {
    'BREAKFAST': Decimal('0.30'),
    'LUNCH': Decimal('0.40'),
    'DINNER': Decimal('0.30'),
}

def find_best_meal_plan(possible_recipes, target_calories, nutrition_targets):
    """
    Подбирает наилучший план питания из доступных рецептов.
    
    Алгоритм использует метод случайного поиска с итерационной подгонкой:
    1. На каждой итерации создается случайный базовый план.
    2. Количество порций в плане итерационно корректируется для приближения к целевой калорийности.
    3. Рассчитывается "штраф" (score) комбинации, учитывающий отклонение от цели по калориям и БЖУ.
    4. После множества попыток выбирается комбинация с наименьшим штрафом.
    """
    
    # 1. Подготовка данных
    #---------------------------------------------------------------------------
    all_recipes_with_nutrition = []
    for recipe in possible_recipes:
        nutrition_info = calculate_recipe_nutrition(recipe)
        # Исключаем рецепты с нулевой калорийностью
        if nutrition_info['calories_per_serving'] > 0:
            all_recipes_with_nutrition.append({'recipe': recipe, 'nutrition': nutrition_info})

    # Распределяем рецепты по "корзинам" для каждого приема пищи.        
    breakfasts = [r for r in all_recipes_with_nutrition if r['recipe'].meal_type == 'BREAKFAST']
    lunches = [r for r in all_recipes_with_nutrition if r['recipe'].meal_type == 'LUNCH']
    dinners = [r for r in all_recipes_with_nutrition if r['recipe'].meal_type == 'DINNER']

    # Если для какого-то приема пищи нет рецептов, составить план невозможно.
    if not breakfasts or not lunches or not dinners:
        return None

    # 2. Инициализация для поиска лучшего решения
    #---------------------------------------------------------------------------
    best_combination = None
    best_score = float('inf') 
    target_calories_decimal = Decimal(target_calories)
    number_of_attempts = 300 # Количество попыток найти лучший план.

    # Шаг 3: Основной цикл поиска.
    #---------------------------------------------------------------------------
    for _ in range(number_of_attempts):
        
        # 3.1. Выбираем случайную базовую комбинацию из трех блюд.
        base_plan_data = {
            'breakfast': random.choice(breakfasts),
            'lunch': random.choice(lunches),
            'dinner': random.choice(dinners)
        }
        
        # Инициализируем порции
        servings = {'breakfast': 1, 'lunch': 1, 'dinner': 1}
        
        # 3.2. Итерационная подгонка порций: пытаемся приблизиться к цели,
        # увеличивая или уменьшая количество порций в течение нескольких шагов.
        for i in range(5):
            current_calories = sum(base_plan_data[mt]['nutrition']['calories_per_serving'] * s for mt, s in servings.items())

            # Если мы уже достаточно близко к цели (в пределах 20%), прекращаем подгонку.    
            if abs(current_calories - target_calories_decimal) / target_calories_decimal <= 0.20:
                break
            
            # Если калорий не хватает, увеличиваем порцию у самого "дефицитного" блюда.
            if current_calories < target_calories_decimal:
                deficits = {}
                for meal_type, data in base_plan_data.items():
                    ideal_calories = target_calories_decimal * IDEAL_MEAL_DISTRIBUTION[meal_type.upper()]
                    actual_calories = data['nutrition']['calories_per_serving'] * servings[meal_type]
                    deficits[meal_type] = ideal_calories - actual_calories
                
                if any(v > 0 for v in deficits.values()):
                    meal_to_increase = max(deficits, key=deficits.get)
                    servings[meal_to_increase] += 1
            # Если калорий слишком много, уменьшаем порцию у самого калорийного блюда.
            elif current_calories > target_calories_decimal:
                meal_calories = {mt: data['nutrition']['calories_per_serving'] * servings[mt] for mt, data in base_plan_data.items()}
                meal_to_decrease = max(meal_calories, key=meal_calories.get)
                if servings[meal_to_decrease] > 1:
                    servings[meal_to_decrease] -= 1
        
        # 3.3. Расчет итоговых показателей и проверка.
        total_calories = sum(base_plan_data[mt]['nutrition']['calories_per_serving'] * s for mt, s in servings.items())
        total_proteins = sum(base_plan_data[mt]['nutrition']['proteins_per_serving'] * s for mt, s in servings.items())
        total_fats = sum(base_plan_data[mt]['nutrition']['fats_per_serving'] * s for mt, s in servings.items())
        total_carbs = sum(base_plan_data[mt]['nutrition']['carbs_per_serving'] * s for mt, s in servings.items())

        # Проверяем, соответствует ли план жестким ограничениям по БЖУ.
        is_valid = True
        if total_proteins < nutrition_targets['proteins'] or total_fats < nutrition_targets['fats']:
            is_valid = False
        if nutrition_targets['carb_constraint_type'] == 'AT_MOST' and total_carbs > nutrition_targets['carbs']:
            is_valid = False
        if nutrition_targets['carb_constraint_type'] == 'AT_LEAST' and total_carbs < nutrition_targets['carbs']:
            is_valid = False
        
        if not is_valid:
            continue    # Если план невалиден, переходим к следующей попытке.

        # 3.4. Расчет "оценки" (штрафа) для валидной комбинации.
        # Штраф = (отклонение по общим калориям)^2 + (штрафы за дисбаланс по приемам пищи).
        score = (total_calories - target_calories_decimal) ** 2
        for meal_type, data in base_plan_data.items():
            ideal_meal_calories = target_calories_decimal * IDEAL_MEAL_DISTRIBUTION[meal_type.upper()]
            current_meal_calories = data['nutrition']['calories_per_serving'] * servings[meal_type]
            score += (current_meal_calories - ideal_meal_calories) ** 2 * Decimal('0.3')    # Коэффициент для штрафа

        # 3.5. Сохранение лучшей комбинации
        if score < best_score:
            best_score = score
            best_combination = {
                'breakfast': {'recipe_data': base_plan_data['breakfast'], 'servings': servings['breakfast']},
                'lunch': {'recipe_data': base_plan_data['lunch'], 'servings': servings['lunch']},
                'dinner': {'recipe_data': base_plan_data['dinner'], 'servings': servings['dinner']},
            }

    # 4. Финальная проверка на адекватность
    if best_combination:
        final_calories = sum(v['recipe_data']['nutrition']['calories_per_serving'] * v['servings'] for v in best_combination.values())
        if final_calories > 0:
            # Если отклонение от цели слишком большое (более 25%), считаем, что подходящего плана нет.
            deviation_percent = abs(final_calories - target_calories_decimal) / target_calories_decimal
            if deviation_percent > Decimal('0.25'):
                return None
    
    return best_combination