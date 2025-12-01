from django.contrib import admin
from django.urls import path
from django.http import HttpResponse
from . import views

app_name = 'politicians'
urlpatterns = [
    path('', views.index, name = "index"),
    path('politician/add/', views.politician_add, name = "politician_add"),
    path('politician/<slug:slug>/', views.politician_view, name = "politician_view"),
    path('politician/<slug:slug>/update/', views.politician_update, name = "politician_update"),
    path('politician/<slug:slug>/record/add/', views.politicianrecord_add, name = "politicianrecord_add"),
    path('politician/<slug:slug>/record/<int:record_id>/update/', views.politicianrecord_update, name = "politicianrecord_update"),
    path('politician/<slug:slug>/record/<int:record_id>/delete/', views.politicianrecord_delete, name = "politicianrecord_delete"),
    # path('customers/', views.listcustomers, name = 'customer-list'),
    # path('customer/new/', views.addcustomer, name = 'customer-add'),
    # path('customer/<int:pk>/', views.detailcustomer, name = 'customer-detail'),
    # path('customer/<int:pk>/update', views.updatecustomer, name = 'customer-update'),
    # path('customer/<int:pk>/delete', views.deletecustomer, name = 'customer-delete'),
    # path('customer/<int:customer_id>/address/new', views.addaddress, name = 'address-add'),
]