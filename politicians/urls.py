from django.contrib import admin
from django.urls import path
from django.http import HttpResponse
from . import views

app_name = 'politicians'
urlpatterns = [
    path('', views.index, name = "index"),
    path('politician/add/', views.politician_add, name = "politician_add"),
    path('politician/graph/', views.plot_graph, name = "graph"),
    path('politician/<slug:slug>/', views.politician_view, name = "politician_view"),
    path('politician/<slug:slug>/update/', views.politician_update, name = "politician_update"),
    path('politician/<slug:slug>/record/add/', views.politicianrecord_add, name = "politicianrecord_add"),
    path('politician/<slug:slug>/record/<int:record_id>/update/', views.politicianrecord_update, name = "politicianrecord_update"),
    path('politician/<slug:slug>/record/<int:record_id>/delete/', views.politicianrecord_delete, name = "politicianrecord_delete"),
]