from django.contrib import admin
from .models import Diet, Ingredient, Recipe, RecipeIngredient

# ==============================================================================
# Настройка админ-панели для модели Diet
# ==============================================================================
@admin.register(Diet)
class DietAdmin(admin.ModelAdmin):
    """Настройки отображения модели Диет в админ-панели."""
    list_display = ('name', 'default_calories', 'carbs_constraint')
    search_fields = ('name',)

# ==============================================================================
# Настройка админ-панели для модели Ingredient
# ==============================================================================
@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Настройки отображения модели Ингредиентов в админ-панели."""
    list_display = ('name', 'calories', 'proteins', 'fats', 'carbs')
    search_fields = ('name',)
    list_per_page = 50 # Отображать по 50 ингредиентов на странице

# ==============================================================================
# Настройка админ-панели для модели Recipe
# ==============================================================================
class RecipeIngredientInline(admin.TabularInline):
    """
    Позволяет редактировать ингредиенты прямо на странице создания/редактирования рецепта.
    Удобнее, чем добавлять их по одному на отдельной странице.
    """
    model = RecipeIngredient
    extra = 1
    autocomplete_fields = ['ingredient']

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Настройки отображения модели Рецептов в админ-панели."""
    inlines = [RecipeIngredientInline]
    
    # Колонки в списке всех рецептов
    list_display = ('name', 'cooking_time', 'meal_type', 'servings')
    
    # Фильтры
    list_filter = ('meal_type', 'diets')
    
    # Поля поиска
    search_fields = ('name', 'description')
    
    # Количество рецептов на странице
    list_per_page = 25