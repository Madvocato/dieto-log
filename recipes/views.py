from django.shortcuts import render, get_object_or_404
from .models import Diet, Recipe
import random
from .utils import calculate_recipe_nutrition

def index(request):
    diets = Diet.objects.all()

    selected_diet = None
    calories_value = 2000 # Задаем глобальный дефолт

    if request.method == 'POST':
        # Получаем данные из формы
        diet_id = request.POST.get('diet')
        target_calories = int(request.POST.get('calories'))
        
        if diet_id:
            selected_diet = Diet.objects.get(id=diet_id)
        if target_calories:
            target_calories = int(target_calories)

        elif diets.exists():
            selected_diet = diets.first()
            target_calories = selected_diet.default_calories
            
    context = {
        'diets': diets,
        'selected_diet': selected_diet,
        'calories_value': calories_value,
        'meal_plan': None,
        'nutrition_targets': None,
    }

    if selected_diet and request.method == 'POST':
        # --- РАСЧЕТ ЦЕЛЕВЫХ ПОРОГОВ БЖУ ---
        calories_factor = target_calories / 1000.0
            
        min_proteins = round(selected_diet.protein_per_1000_kcal * calories_factor)
        min_fats = round(selected_diet.fat_per_1000_kcal * calories_factor)
        carb_threshold = round(selected_diet.carb_per_1000_kcal * calories_factor)
            
        # Добавляем рассчитанные пороги в контекст для отображения
        context['nutrition_targets'] = {
            'proteins': min_proteins,
            'fats': min_fats,
            'carbs': carb_threshold,
            'carb_constraint_text': selected_diet.get_carbs_constraint_display(),
            'carb_constraint_type': selected_diet.carbs_constraint
        }
        # --- АЛГОРИТМ (ПОКА ЧТО СЛУЧАЙНЫЙ) ---
        
        # Фильтрует рецепты по выбранной диете
        possible_recipes = Recipe.objects.filter(diets=selected_diet)
        breakfasts = possible_recipes.filter(meal_type='BREAKFAST')
        lunches = possible_recipes.filter(meal_type='LUNCH')
        dinners = possible_recipes.filter(meal_type='DINNER')

        # Выбираем случайные рецепты и сразу обогащаем их данными о КБЖУ
        meal_plan = {}
            
        breakfast_recipe = random.choice(list(breakfasts)) if breakfasts else None
        if breakfast_recipe:
            meal_plan['breakfast'] = {
                'recipe': breakfast_recipe,
                'nutrition': calculate_recipe_nutrition(breakfast_recipe)
            }

        lunch_recipe = random.choice(list(lunches)) if lunches else None
        if lunch_recipe:
            meal_plan['lunch'] = {
                'recipe': lunch_recipe,
                'nutrition': calculate_recipe_nutrition(lunch_recipe)
            }

        dinner_recipe = random.choice(list(dinners)) if dinners else None
        if dinner_recipe:
            meal_plan['dinner'] = {
                'recipe': dinner_recipe,
                'nutrition': calculate_recipe_nutrition(dinner_recipe)
            }
            
        context['meal_plan'] = meal_plan

    return render(request, 'recipes/index.html', context)

def recipe_detail(request, recipe_id):
    # get_object_or_404 - удобная функция Django.
    # Она пытается найти объект, и если не находит - автоматически показывает страницу 404.
    recipe = get_object_or_404(Recipe, pk=recipe_id)
    
    # Используем наш уже готовый калькулятор для этого рецепта
    nutrition = calculate_recipe_nutrition(recipe)
    
    context = {
        'recipe': recipe,
        'nutrition': nutrition,
    }
    
    return render(request, 'recipes/recipe_detail.html', context)
