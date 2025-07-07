from django.shortcuts import render
from .models import Diet, Recipe
import random

def index(request):
    diets = Diet.objects.all()
    meal_plan = None

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

        # Просто выбирает по одному случайному рецепту
        meal_plan = {
            'breakfast': random.choice(list(breakfasts)) if breakfasts else None,
            'lunch': random.choice(list(lunches)) if lunches else None,
            'dinner': random.choice(list(dinners)) if dinners else None,
        }
        
        # --- КОНЕЦ АЛГОРИТМА ---

    context = {
        'diets': diets,
        'meal_plan': meal_plan,
    }

    return render(request, 'recipes/index.html', context)
