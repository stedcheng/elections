from django.contrib import admin
from .models import Politician, PoliticianRecord, Province, Region

# Register your models here.
admin.site.register([Politician, PoliticianRecord, Province, Region])
