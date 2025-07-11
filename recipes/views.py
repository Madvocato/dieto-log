from django.shortcuts import render, get_object_or_404
from .models import Diet, Recipe, Ingredient
from .utils import calculate_recipe_nutrition
from .generator import find_best_meal_plan
from decimal import Decimal
from django.db import models


# ==============================================================================
# View для главной страницы (генератор меню)
# ==============================================================================
def index(request):
    """
    Отображает главную страницу с формой генерации меню.
    При POST-запросе обрабатывает данные, запускает генератор и выводит результат.
    """
    # Шаг 1: Подготовка данных для формы.
    # Ставим "Сбалансированную" диету первой в списке для удобства.
    try:
        balanced_diet = Diet.objects.get(name="Сбалансированная")
        other_diets = Diet.objects.exclude(name="Сбалансированная").order_by('name')
        all_diets = [balanced_diet] + list(other_diets)
    except Diet.DoesNotExist:
        all_diets = list(Diet.objects.all().order_by('name'))

    # --- ЭТАП 2: Инициализация контекста для первого захода на страницу (GET) ---
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
            target_calories = int(request.POST.get('calories', 2000))
            selected_diet = get_object_or_404(Diet, id=diet_id)
            
            # Обновляем контекст, чтобы "запомнить" выбор пользователя
            context.update({
                'selected_diet': selected_diet,
                'calories_value': target_calories,
            })

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
            
            # Запуск генератора
            possible_recipes = Recipe.objects.filter(diets=selected_diet)
            targets_for_generator = nutrition_targets.copy()
            targets_for_generator.pop('carb_constraint_text')
            meal_plan_raw = find_best_meal_plan(possible_recipes, target_calories, targets_for_generator)
        
            # Обработка результата генератора
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
            context['error_message'] = "Произошла ошибка. Пожалуйста, проверьте введенные данные и попробуйте снова."
    
    return render(request, 'recipes/index.html', context)


# ==============================================================================
# View для детальной страницы рецепта
# ==============================================================================
def recipe_detail(request, recipe_id):
    """
    Отображает страницу с полной информацией о конкретном рецепте,
    включая ингредиенты, инструкцию и рассчитанный КБЖУ.
    """
    recipe = get_object_or_404(Recipe, pk=recipe_id)
    nutrition = calculate_recipe_nutrition(recipe)
    context = {
        'recipe': recipe,
        'nutrition': nutrition,
    }
    return render(request, 'recipes/recipe_detail.html', context)


# ==============================================================================
# View для каталога рецептов
# ==============================================================================
def recipe_list(request):
    """
    Отображает страницу с каталогом всех рецептов.
    Реализует сложную фильтрацию и сортировку на основе GET-параметров.
    """
    recipes = Recipe.objects.filter(is_simple_ingredient=False)
    diets = Diet.objects.all().order_by('name')
    meal_types = Recipe.MEAL_TYPE_CHOICES

# --- Получаем все GET-параметры из URL для фильтрации и сортировки ---
    selected_diet_id = request.GET.get('diet')
    selected_meal_type = request.GET.get('meal_type')
    max_cooking_time = request.GET.get('max_time')
    included_ingredients = request.GET.getlist('ingredients')
    search_query = request.GET.get('q')
    sort_by = request.GET.get('sort', 'name') # По умолчанию сортируем по названию
    
    # Последовательно применяем фильтры
    if selected_diet_id and selected_diet_id.isdigit():
        recipes = recipes.filter(diets__id=selected_diet_id)

    if selected_meal_type:
        recipes = recipes.filter(meal_type=selected_meal_type)

    if max_cooking_time and max_cooking_time.isdigit():
        recipes = recipes.filter(cooking_time__lte=max_cooking_time)

    # Фильтр по ингредиентам: рецепт должен содержать КАЖДЫЙ из выбранных ингредиентов.
    if included_ingredients:
        for ingredient_id in included_ingredients:
            if ingredient_id.isdigit(): # Добавлена проверка на случай мусора в GET-параметрах
                recipes = recipes.filter(ingredients__id=ingredient_id)

    # Фильтруем по поисковому запросу, если он есть
    if search_query:
        recipes = recipes.filter(
            models.Q(name__icontains=search_query) | 
            models.Q(description__icontains=search_query) |
            models.Q(ingredients__name__icontains=search_query)
        ).distinct()

    # --- Применяем сортировку ---
    VALID_SORT_FIELDS = ['name', 'cooking_time', 'servings']

    # Проверяем, что поле для сортировки (без знака "-") находится в нашем "списке"
    if sort_by.lstrip('-') in VALID_SORT_FIELDS:
        recipes = recipes.order_by(sort_by)
    else:
        # Если в URL передан невалидный параметр сортировки, применяем сортировку по умолчанию.
        sort_by = 'name'
        recipes = recipes.order_by(sort_by)

    context = {
        'recipes': recipes,
        'diets': diets,
        'meal_types': meal_types,
        'ingredients_all': Ingredient.objects.all(),
        # Передаем обратно в шаблон, чтобы "запомнить" выбор пользователя
        'selected_diet_id': int(selected_diet_id) if selected_diet_id and selected_diet_id.isdigit() else None,
        'selected_meal_type': selected_meal_type,
        'search_query': search_query,
        'current_sort': sort_by,
        'max_cooking_time': max_cooking_time,
        'selected_ingredients': [int(i) for i in included_ingredients if i.isdigit()],
    }
    
    return render(request, 'recipes/recipe_list.html', context)