from django.forms import ModelForm, HiddenInput
from .models import Politician, PoliticianRecord

class PoliticianForm(ModelForm):
    class Meta:
        model = Politician, PoliticianRecord
        fields = ['last_name', 'first_name', 'middle_name', 'position', 'party', 'year', 'province', 'region']
        widget = {'position_weight' : HiddenInput()}