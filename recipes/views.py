from django.shortcuts import render, get_object_or_404
from .models import Diet, Recipe, Ingredient
from .utils import calculate_recipe_nutrition
from .generator import find_best_meal_plan
from decimal import Decimal
from django.db import models
from django.db.models.functions import Lower

def index(request):
    try:
        balanced_diet = Diet.objects.get(name="Сбалансированная")
        other_diets = Diet.objects.exclude(name="Сбалансированная").order_by('name')
        diets = [balanced_diet] + list(other_diets)
    except Diet.DoesNotExist:
        diets = list(Diet.objects.all().order_by('name'))
    
    # --- ОПРЕДЕЛЕНИЕ ВХОДНЫХ ПАРАМЕТРОВ ---

    if request.method == 'POST':
        # Если форма отправлена, берем данные из нее
        try:
            diet_id = int(request.POST.get('diet'))
            calories_value = int(request.POST.get('calories'))
            selected_diet = Diet.objects.get(id=diet_id)
        except (ValueError, TypeError, Diet.DoesNotExist):
            # Если данные кривые, сбрасываем на дефолт
            selected_diet = diets[0] if diets else None
            calories_value = selected_diet.default_calories if selected_diet else 2000
    else:
        # Если страница загружается первый раз (GET), берем дефолтные значения
        selected_diet = diets[0] if diets else None
        calories_value = selected_diet.default_calories if selected_diet else 2000

    # --- ВЫЧИСЛЕНИЯ И ГЕНЕРАЦИЯ (ТОЛЬКО ДЛЯ POST) ---

    nutrition_targets = None
    meal_plan = None
    error_message = None

    if request.method == 'POST' and selected_diet:
        # Рассчитываем целевые пороги БЖУ
        calories_factor = Decimal(calories_value) / Decimal(1000.0)
        nutrition_targets = {
            'proteins': round(selected_diet.protein_per_1000_kcal * calories_factor),
            'fats': round(selected_diet.fat_per_1000_kcal * calories_factor),
            'carbs': round(selected_diet.carb_per_1000_kcal * calories_factor),
            'carb_constraint_type': selected_diet.carbs_constraint,
            'carb_constraint_text': selected_diet.get_carbs_constraint_display()
        }
        
        # Вызываем "умный" генератор
        possible_recipes = Recipe.objects.filter(diets=selected_diet)
        targets_for_generator = nutrition_targets.copy()
        targets_for_generator.pop('carb_constraint_text')
        
        meal_plan = find_best_meal_plan(possible_recipes, calories_value, targets_for_generator)
        
        # Обрабатываем результат генератора
        if meal_plan is None:
            error_message = "К сожалению, не удалось составить меню. Попробуйте изменить калорийность или добавить больше рецептов для этой диеты."

    # --- ЭТАП 3: ФОРМИРОВАНИЕ КОНТЕКСТА И ОТПРАВКА ---

    context = {
        'diets': diets,
        'selected_diet': selected_diet if selected_diet else None,
        'calories_value': calories_value,
        'meal_plan': meal_plan,
        'nutrition_targets': nutrition_targets,
        'error_message': error_message,
    }
    
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
    recipes = Recipe.objects.all()
    diets = Diet.objects.all().order_by('name')
    meal_types = Recipe.MEAL_TYPE_CHOICES

    # --- ЛОГИКА ФИЛЬТРАЦИИ ---
    
    selected_diet_id = request.GET.get('diet')
    selected_meal_type = request.GET.get('meal_type')
    max_cooking_time = request.GET.get('max_time')
    included_ingredients = request.GET.getlist('ingredients')
    search_query = request.GET.get('q')
    

    sort_by = request.GET.get('sort', 'name')

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

    if sort_by in ['name', 'cooking_time', 'servings']: # Проверка на допустимые значения
        recipes = recipes.order_by(sort_by)
    else:
        recipes = recipes.order_by('name')

    context = {
        'recipes': recipes,
        'diets': diets,
        'meal_types': meal_types,
        # Передаем обратно в шаблон, чтобы "запомнить" выбор пользователя
        'selected_diet_id': int(selected_diet_id) if selected_diet_id and selected_diet_id.isdigit() else None,
        'selected_meal_type': selected_meal_type,
        'search_query': search_query,
        'current_sort': sort_by,
        'max_cooking_time': max_cooking_time,
        'ingredients_all': Ingredient.objects.all(),
        'selected_ingredients': [int(i) for i in included_ingredients],
    }
    
    return render(request, 'recipes/recipe_list.html', context)