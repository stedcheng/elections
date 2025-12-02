from django.forms import ModelForm
from .models import Politician, PoliticianRecord

class PoliticianForm(ModelForm):
    class Meta:
        model = Politician
        fields = ['first_name', 'middle_name', 'last_name']

class PoliticianRecordForm(ModelForm):
    class Meta:
        model = PoliticianRecord
        fields = ['position', 'party', 'year', 'region', 'province', 'community']