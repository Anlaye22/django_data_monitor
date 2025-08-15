import logging
import json
from collections import defaultdict

import requests
from django.conf import settings
from django.shortcuts import render
from django.views import View
from django.http import HttpResponse

# Configura un logger para manejar errores de forma más robusta
logger = logging.getLogger(__name__)

# --- Vistas del Proyecto ---

class APIAnalyticsView(View):
    """
    Vista que procesa y visualiza datos de una API externa.
    Usa la arquitectura de renderizado del lado del servidor (SSR) para generar el dashboard.
    """
    template_name = "dashboard/index.html"

    def get(self, request, *args, **kwargs):
        """Maneja las peticiones GET para mostrar el panel de control."""
        api_data = self._fetch_api_data()
        
        if api_data.get('error_message'):
            context = self._get_error_context(api_data['error_message'])
        else:
            processed_data = self._process_posts(api_data['posts'])
            context = self._build_context(processed_data)

        return render(request, self.template_name, context)

    def _fetch_api_data(self):
        """
        Intenta obtener datos de la API. Devuelve un diccionario con 'posts' o 'error_message'.
        """
        try:
            print(f"Intentando conectar a la API en: {settings.API_URL}")
            response = requests.get(settings.API_URL, timeout=8)
            response.raise_for_status()
            posts = response.json()
            print(f"API conectada con éxito. Se recibieron {len(posts)} posts.")
            return {'posts': posts}
        except requests.exceptions.RequestException as e:
            logger.error(f"Fallo en la conexión con la API: {e}")
            print(f"Error en la conexión con la API: {e}")
            return {'error_message': 'No se pudo conectar a la fuente de datos externa.'}

    def _process_posts(self, posts):
        """Calcula métricas e indicadores a partir de una lista de posts."""
        if not posts:
            return self._get_default_metrics()

        total_posts = len(posts)
        user_ids = [post['userId'] for post in posts]
        unique_users = len(set(user_ids))
        
        title_lengths = [len(post['title']) for post in posts]
        avg_title_len = sum(title_lengths) / total_posts if total_posts else 0

        user_post_counts = defaultdict(int)
        for user_id in user_ids:
            user_post_counts[user_id] += 1

        sorted_counts = sorted(user_post_counts.items())
        chart_labels = [f"User {uid}" for uid, _ in sorted_counts]
        chart_values = [count for _, count in sorted_counts]

        return {
            'total_posts': total_posts,
            'unique_users': unique_users,
            'avg_title_len': round(avg_title_len, 2),
            'chart_labels': chart_labels,
            'chart_values': chart_values,
            'posts_list': posts[:20],
        }

    def _get_default_metrics(self):
        """Devuelve un diccionario de métricas con valores predeterminados."""
        return {
            'total_posts': 0,
            'unique_users': 0,
            'avg_title_len': 0,
            'chart_labels': [],
            'chart_values': [],
            'posts_list': [],
        }

    def _build_context(self, data):
        """Construye el diccionario de contexto final para la plantilla."""
        return {
            'page_title': "Panel de Datos de la API 📊",
            'post_items': data['posts_list'],
            'posts_count': data['total_posts'],
            'users_count': data['unique_users'],
            'average_title_length': data['avg_title_len'],
            'graph_labels': json.dumps(data['chart_labels']),
            'graph_values': json.dumps(data['chart_values']),
            'error_message': None,
        }

    def _get_error_context(self, message):
        """Genera un contexto con valores por defecto y un mensaje de error."""
        return {
            'page_title': "Panel de Datos de la API 📊",
            'post_items': [],
            'posts_count': 0,
            'users_count': 0,
            'average_title_length': 0,
            'graph_labels': '[]',
            'graph_values': '[]',
            'error_message': message,
        }