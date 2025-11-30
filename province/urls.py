from django.urls import path
from . import views

urlpatterns = [
    path('', views.province_analysis, name='province_analysis'),
]