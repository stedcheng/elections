from django.contrib import admin

# Register your models here.
from .models import Politician, Province, Region, PoliticianRecord
admin.site.register([Politician, Province, Region, PoliticianRecord])