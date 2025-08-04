from django.shortcuts import render
from django.http import HttpResponse
import requests
from django.conf import settings

# Create your views here.
def index(request):
    #return HttpResponse("Hello, world. You're at the dashboard index.")
    #return render(request, 'dashboard/index.html')

    response = requests.get(settings.API_URL)  # URL de la API
    posts = response.json()  # Convertir la respuesta a JSON

    # Número total de respuestas
    total_responses = len(posts)

    data = {
        'title': "Landing Page' Dashboard",
        'total_responses': total_responses,
    }
    return render(request, 'dashboard/index.html', data)