from django.shortcuts import render, get_object_or_404
from .models import Diet, Recipe, Ingredient
from .utils import calculate_recipe_nutrition
from .generator import find_best_meal_plan
from decimal import Decimal
from django.db import models
from django.db.models.functions import Lower

def index(request):
    # --- ЭТАП 1: ПОДГОТОВКА ДАННЫХ ДЛЯ ФОРМЫ ---
    try:
        balanced_diet = Diet.objects.get(name="Сбалансированная")
        other_diets = Diet.objects.exclude(name="Сбалансированная").order_by('name')
        all_diets = [balanced_diet] + list(other_diets)
    except Diet.DoesNotExist:
        all_diets = list(Diet.objects.all().order_by('name'))

    # --- ЭТАП 2: ИНИЦИАЛИЗАЦИЯ КОНТЕКСТА ---
    # Создаем ОДИН context и сразу кладем в него все, что нужно для отрисовки страницы
    context = {
        'diets': all_diets,
        'selected_diet': all_diets[0] if all_diets else None,
        'calories_value': (all_diets[0].default_calories if all_diets else 2000),
        'meal_plan': None,
        'total_nutrition': None,
        'nutrition_targets': None,
        'error_message': None,
    }

    # --- ЭТАП 3: ОБРАБОТКА POST-ЗАПРОСА ---
    if request.method == 'POST':
        try:
            # Получаем данные от пользователя
            diet_id = int(request.POST.get('diet'))
            target_calories = int(request.POST.get('calories'))
            selected_diet = Diet.objects.get(id=diet_id)
            
            # Обновляем значения в контексте для "запоминания" выбора
            context['selected_diet'] = selected_diet
            context['calories_value'] = target_calories

            # Рассчитываем и обновляем в контексте целевые пороги БЖУ
            calories_factor = Decimal(target_calories) / Decimal(1000)
            nutrition_targets = {
                'proteins': round(selected_diet.protein_per_1000_kcal * calories_factor),
                'fats': round(selected_diet.fat_per_1000_kcal * calories_factor),
                'carbs': round(selected_diet.carb_per_1000_kcal * calories_factor),
                'carb_constraint_type': selected_diet.carbs_constraint,
                'carb_constraint_text': selected_diet.get_carbs_constraint_display()
            }
            context['nutrition_targets'] = nutrition_targets
            
            # Вызываем генератор
            possible_recipes = Recipe.objects.filter(diets=selected_diet)
            targets_for_generator = nutrition_targets.copy()
            targets_for_generator.pop('carb_constraint_text')
            meal_plan_raw = find_best_meal_plan(possible_recipes, target_calories, targets_for_generator)
        
            # Обрабатываем результат генератора
            if meal_plan_raw:
                final_plan_for_template = {}
                total_nutrition = {'calories': 0, 'proteins': 0, 'fats': 0, 'carbs': 0}

                for meal_type, data in meal_plan_raw.items():
                    recipe_data = data['recipe_data']
                    servings = data['servings']
                    
                    # Масштабируем КБЖУ на количество порций
                    nutrition = {key: value * servings for key, value in recipe_data['nutrition'].items() if 'per_serving' in key}
                    
                    final_plan_for_template[meal_type] = {
                        'recipe': recipe_data['recipe'],
                        'servings': servings,
                        'nutrition': nutrition,
                    }
                    
                    total_nutrition['calories'] += nutrition['calories_per_serving']
                    total_nutrition['proteins'] += nutrition['proteins_per_serving']
                    total_nutrition['fats'] += nutrition['fats_per_serving']
                    total_nutrition['carbs'] += nutrition['carbs_per_serving']
                
                context['meal_plan'] = final_plan_for_template
                context['total_nutrition'] = total_nutrition
            else:
                context['error_message'] = "К сожалению, не удалось составить меню..."

        except (ValueError, TypeError, Diet.DoesNotExist):
            context['error_message'] = "Произошла ошибка. Пожалуйста, проверьте введенные данные."
    
    return render(request, 'recipes/index.html', context)


def recipe_detail(request, recipe_id):
    recipe = get_object_or_404(Recipe, pk=recipe_id)
    nutrition = calculate_recipe_nutrition(recipe)
    context = {
        'recipe': recipe,
        'nutrition': nutrition,
    }
    return render(request, 'recipes/recipe_detail.html', context)

def recipe_list(request):
    recipes = Recipe.objects.filter(is_simple_ingredient=False).order_by('name')
    diets = Diet.objects.all().order_by('name')
    meal_types = Recipe.MEAL_TYPE_CHOICES

    # --- ЛОГИКА ФИЛЬТРАЦИИ ---
    
    selected_diet_id = request.GET.get('diet')
    selected_meal_type = request.GET.get('meal_type')
    max_cooking_time = request.GET.get('max_time')
    included_ingredients = request.GET.getlist('ingredients')
    search_query = request.GET.get('q')
    
    # Фильтруем по диете, если она выбрана
    if selected_diet_id and selected_diet_id.isdigit():
        recipes = recipes.filter(diets__id=selected_diet_id)

    if selected_meal_type:
        recipes = recipes.filter(meal_type=selected_meal_type)

    if max_cooking_time and max_cooking_time.isdigit():
        recipes = recipes.filter(cooking_time__lte=max_cooking_time)

    if included_ingredients:
        for ingredient_id in included_ingredients:
            recipes = recipes.filter(ingredients__id=ingredient_id)

    # Фильтруем по поисковому запросу, если он есть
    if search_query:
        recipes = recipes.filter(
            models.Q(name__icontains=search_query) | 
            models.Q(description__icontains=search_query) |
            models.Q(ingredients__name__icontains=search_query)
        ).distinct()

    sort_by = request.GET.get('sort', 'name')
    VALID_SORT_FIELDS = ['name', 'cooking_time', 'servings']
    
    field_to_sort = sort_by.lstrip('-')
    if field_to_sort in VALID_SORT_FIELDS:
        recipes = recipes.order_by(sort_by)
    else:
        recipes = recipes.order_by('name')
        sort_by = 'name'

    SORT_OPTIONS = {
        'name': 'Название (А-Я)',
        '-name': 'Название (Я-А)',
        'cooking_time': 'Время (быстрые)',
        '-cooking_time': 'Время (долгие)',
    }

    if field_to_sort not in VALID_SORT_FIELDS:
        sort_by = 'name'

    context = {
        'recipes': recipes,
        'diets': diets,
        'meal_types': meal_types,
        # Передаем обратно в шаблон, чтобы "запомнить" выбор пользователя
        'selected_diet_id': int(selected_diet_id) if selected_diet_id and selected_diet_id.isdigit() else None,
        'selected_meal_type': selected_meal_type,
        'search_query': search_query,
        'current_sort': sort_by,
        'sort_options': SORT_OPTIONS,
        'max_cooking_time': max_cooking_time,
        'ingredients_all': Ingredient.objects.all(),
        'selected_ingredients': [int(i) for i in included_ingredients],
    }
    
    return render(request, 'recipes/recipe_list.html', context)