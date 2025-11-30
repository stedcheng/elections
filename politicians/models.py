from django.db import models
import pandas as pd

# Create your models here.

class Politician(models.Model):
    last_name = models.CharField(max_length = 100)
    first_name = models.CharField(max_length = 100)
    middle_name = models.CharField(max_length = 100, blank = True, null = True)

    def __str__(self):
        return f"{self.first_name} {self.middle_name or ''} {self.last_name}".strip()

class Region(models.Model):
    name = models.CharField(max_length = 100, unique = True)

    def __str__(self):
        return self.name

class Province(models.Model):
    name = models.CharField(max_length = 100, unique = True)
    region = models.ForeignKey(Region, on_delete = models.CASCADE)

    def __str__(self):
        return self.name

class PoliticianRecord(models.Model):
    politician = models.ForeignKey(Politician, on_delete = models.CASCADE)
    region = models.ForeignKey(Region, on_delete = models.PROTECT)
    province = models.ForeignKey(Province, on_delete = models.PROTECT)

    position_choices = [
    ("COUNCILOR", "COUNCILOR"),
    ("PROVINCIAL BOARD MEMBER", "PROVINCIAL BOARD MEMBER"),
    ("VICE MAYOR", "VICE MAYOR"),
    ("VICE GOVERNOR", "VICE GOVERNOR"),
    ("MAYOR", "MAYOR"),
    ("MEMBER, HOUSE OF REPRESENTATIVES", "MEMBER, HOUSE OF REPRESENTATIVES"),
    ("GOVERNOR", "GOVERNOR"),
    ]
    position = models.CharField(max_length = 100, choices = position_choices)

    party = models.CharField(max_length = 100, blank = True, null = True)

    year_choices = {(year, year) for year in range(2004, 2023, 3)}
    year = models.IntegerField(choices = year_choices)
    
    position_weight_dict = {
        'COUNCILOR' : 2,
        'PROVINCIAL BOARD MEMBER' : 2,
        'VICE MAYOR' : 3,
        'VICE GOVERNOR' : 3,
        'MAYOR' : 5,
        'MEMBER, HOUSE OF REPRESENTATIVES' : 5,
        'GOVERNOR' : 5
    }
    
    def position_weight(self):
        return self.position_weight_dict.get(self.position, 0)

    def __str__(self):
        return f"Politician {self.politician.first_name} {self.politician.middle_name} {self.politician.last_name}: {self.position} of {self.province}, {self.region} in {self.year}..."
