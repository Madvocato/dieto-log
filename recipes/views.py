from django.shortcuts import render
from .models import Diet, Recipe
import random
from .utils import calculate_recipe_nutrition

def index(request):
    diets = Diet.objects.all()
    meal_plan_with_nutrition = None

    if request.method == 'POST':
        # Получаем данные из формы
        diet_id = request.POST.get('diet')
        calories = int(request.POST.get('calories')) # Превращаем в число

        # --- АЛГОРИТМ (ПОКА ЧТО СЛУЧАЙНЫЙ) ---
        
        # Фильтрует рецепты по выбранной диете
        possible_recipes = Recipe.objects.filter(diets__id=diet_id)

        # Разделяет их по приемам пищи
        breakfasts = possible_recipes.filter(meal_type='BREAKFAST') 
        lunches = possible_recipes.filter(meal_type='LUNCH')
        dinners = possible_recipes.filter(meal_type='DINNER')

        breakfast_recipe = random.choice(list(breakfasts)) if breakfasts else None
        lunch_recipe = random.choice(list(lunches)) if lunches else None
        dinner_recipe = random.choice(list(dinners)) if dinners else None
    
        # Создаем словарь, где для каждого рецепта будет его КБЖУ
        meal_plan_with_nutrition = {}
        if breakfast_recipe:
            meal_plan_with_nutrition['breakfast'] = {
                'recipe': breakfast_recipe,
                'nutrition': calculate_recipe_nutrition(breakfast_recipe)
            }
        if lunch_recipe:
            meal_plan_with_nutrition['lunch'] = {
                'recipe': lunch_recipe,
                'nutrition': calculate_recipe_nutrition(lunch_recipe)
            }
        if dinner_recipe:
            meal_plan_with_nutrition['dinner'] = {
                'recipe': dinner_recipe,
                'nutrition': calculate_recipe_nutrition(dinner_recipe)
            }
        # --- КОНЕЦ АЛГОРИТМА ---

    context = {
        'diets': diets,
        'meal_plan': meal_plan_with_nutrition,
    }

    return render(request, 'recipes/index.html', context)
