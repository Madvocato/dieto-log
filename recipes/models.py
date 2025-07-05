from django.db import models

# Модель 1: Диета (Кето, Веган и т.д.)
class Diet(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название диеты")
    description = models.TextField(blank=True, verbose_name="Описание")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Диета"
        verbose_name_plural = "Диеты"


# Модель 2: Ингредиент (с его КБЖУ на 100г)
class Ingredient(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название ингредиента")
    calories = models.DecimalField(max_digits=7, decimal_places=2, verbose_name="Калории (на 100г)")
    proteins = models.DecimalField(max_digits=7, decimal_places=2, verbose_name="Белки (на 100г)")
    fats = models.DecimalField(max_digits=7, decimal_places=2, verbose_name="Жиры (на 100г)")
    carbs = models.DecimalField(max_digits=7, decimal_places=2, verbose_name="Углеводы (на 100г)")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"


# Модель 3: Рецепт (основная сущность)
class Recipe(models.Model):
    MEAL_TYPE_CHOICES = [
        ('BREAKFAST', 'Завтрак'),
        ('LUNCH', 'Обед'),
        ('DINNER', 'Ужин'),
        ('SNACK', 'Перекус'),
    ]

    name = models.CharField(max_length=200, verbose_name="Название рецепта")
    description = models.TextField(verbose_name="Краткое описание")
    instructions = models.TextField(verbose_name="Инструкция по приготовлению")
    cooking_time = models.PositiveIntegerField(verbose_name="Время приготовления (мин)")
    meal_type = models.CharField(max_length=10, choices=MEAL_TYPE_CHOICES, verbose_name="Тип приема пищи")
    
    # Связь "многие-ко-многим" с диетами
    diets = models.ManyToManyField(Diet, related_name="recipes", verbose_name="Подходящие диеты")
    
    # Связь "многие-ко-многим" с ингредиентами через нашу кастомную модель
    ingredients = models.ManyToManyField(Ingredient, through='RecipeIngredient', related_name="recipes", verbose_name="Ингредиенты")
    
    image = models.ImageField(upload_to='recipe_images/', blank=True, null=True, verbose_name="Изображение")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"

# Модель 4: Связующая таблица для Рецептов и Ингредиентов
# Она нужна, чтобы указать КОЛИЧЕСТВО каждого ингредиента в рецепте
class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, verbose_name="Рецепт")
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, verbose_name="Ингредиент")
    weight_grams = models.PositiveIntegerField(verbose_name="Вес (в граммах)")

    def __str__(self):
        return f"{self.recipe.name} - {self.ingredient.name} ({self.weight_grams}г)"

    class Meta:
        verbose_name = "Ингредиент в рецепте"
        verbose_name_plural = "Ингредиенты в рецептах"
        unique_together = ('recipe', 'ingredient')
