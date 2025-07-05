from django.contrib import admin
from .models import Diet, Ingredient, Recipe, RecipeIngredient

class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1 # По умолчанию показывать 1 пустую строку для добавления

class RecipeAdmin(admin.ModelAdmin):
    # Добавляем инлайн-редактирование ингредиентов
    inlines = [RecipeIngredientInline]
    # Улучшаем отображение списка рецептов
    list_display = ('name', 'cooking_time', 'meal_type')
    # Добавляем фильтры
    list_filter = ('meal_type', 'diets')
    # Добавляем поиск
    search_fields = ('name', 'description')

class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'calories', 'proteins', 'fats', 'carbs')
    search_fields = ('name',)

admin.site.register(Diet)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)