from django.forms import ModelForm, HiddenInput
from .models import Politician, Region, Province, PoliticianRecord

class PoliticianForm(ModelForm):
    class Meta:
        model = Politician
        fields = ['first_name', 'middle_name', 'last_name']

class PoliticianRecordForm(ModelForm):
    class Meta:
        model = PoliticianRecord
        fields = ['position', 'party', 'year', 'region', 'province']
        
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            
            # Temporarily disables the province field if the region field is empty
            self.fields['province'].queryset = Province.objects.none()
            self.fields['province'].disabled = True

            if 'region' in self.data:
                try:
                    region_id = int(self.data.get('region'))
                    self.fields['province'].queryset = Province.objects.filter(region_id = region_id)
                    self.fields['province'].disabled = False
                except:
                    pass

            elif self.instance.pk:
                self.fields['province'].queryset = Province.objects.filter(region = self.instance.region)
                self.fields['province'].disabled = False