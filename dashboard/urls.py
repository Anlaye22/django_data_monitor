from django.urls import path
from .views import APIAnalyticsView

urlpatterns = [
    path('', APIAnalyticsView.as_view(), name='dashboard'),
]