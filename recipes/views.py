from django.shortcuts import render
from .models import Diet

def index(request):
    diets = Diet.objects.all()

    context = {
        'diets': diets,
    }

    return render(request, 'recipes/index.html', context)
