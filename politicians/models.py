import pandas as pd
from django.db import models

# Create your models here.

# Existing Database
df = pd.read_csv("datasets/Political Dynasty v9.csv")

class Politician(models.Model):
    # Not sure whether we should activate blank and null for all fields
    last_name = models.CharField(max_length = 100, blank = True, null = True)
    first_name = models.CharField(max_length = 100, blank = True, null = True)
    middle_name = models.CharField(max_length = 100, blank = True, null = True)

    def __str__(self):
        return f"Politician {self.id}: {self.first_name} {self.middle_name} {self.last_name}"
    
class PoliticianRecord(models.Model):
    politician = models.ForeignKey(Politician, on_delete = models.CASCADE)

    position_choices = {(pos, pos) for pos in df['Position'].unique()}
    position = models.CharField(max_length = 100, choices = position_choices)

    party = models.CharField(max_length = 100, blank = True, null = True)

    year_choices = {(year, year) for year in df['Year'].unique()}
    year = models.IntegerField(choices = year_choices)

    region_choices = {(reg, reg) for reg in df['Region'].unique()}
    region = models.CharField(max_length = 100, choices = region_choices)
    province_choices = {(prov, prov) for prov in df[df['Region'] == region]['Province'].unique()}
    province = models.CharField(max_length = 100, choices = province_choices)
    
    position_weight_dict = {
        'COUNCILOR' : 2,
        'PROVINCIAL BOARD MEMBER' : 2,
        'VICE MAYOR' : 3,
        'VICE GOVERNOR' : 3,
        'MAYOR' : 5,
        'MEMBER, HOUSE OF REPRESENTATIVES' : 5,
        'GOVERNOR' : 5
    }
    position_weight = models.IntegerField(choices = position_weight_dict)

    def __str__(self):
        return f"Politician {self.politician.first_name} {self.politician.middle_name} {self.politician.last_name}: {self.position} of {self.province}, {self.region} in {self.year}..."
