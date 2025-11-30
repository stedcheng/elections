from django.contrib import admin
from django.urls import path
from django.http import HttpResponse
from . import views

app_name = 'politicians'
urlpatterns = [
    path('', views.index),
    path('politician/<politician_name>/', views.politician_view, name = "politician_view"),
    path('politician/add/', views.politician_add),
    path('politician/<politician_name>/update/', views.politician_update),
    path('politician/<politician_name>/record/<int:record_id>/update/', views.politicianrecord_update),
    path('politician/<politician_name>/record/<int:record_id>/delete/', views.politicianrecord_delete),
    # path('customers/', views.listcustomers, name = 'customer-list'),
    # path('customer/new/', views.addcustomer, name = 'customer-add'),
    # path('customer/<int:pk>/', views.detailcustomer, name = 'customer-detail'),
    # path('customer/<int:pk>/update', views.updatecustomer, name = 'customer-update'),
    # path('customer/<int:pk>/delete', views.deletecustomer, name = 'customer-delete'),
    # path('customer/<int:customer_id>/address/new', views.addaddress, name = 'address-add'),
]