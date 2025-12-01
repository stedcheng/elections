from django.shortcuts import render, redirect, get_object_or_404
from .models import custom_slugify, Politician, PoliticianRecord
from .forms import PoliticianForm, PoliticianRecordForm
from django.http import HttpResponse
from django.contrib import messages
import numpy as np
from django.utils.text import slugify

# Create your views here.

# Landing page
def index(request):
    return HttpResponse("[TEMPORARY TEXT] You are at the politicians app page.")

# View a specific politician's details and records.
def politician_view(request, slug):
    # Extract the politician and their records.
    politician = Politician.objects.get(slug = slug)
    records = PoliticianRecord.objects.filter(politician = politician)
    context = {
        'politician': politician,
        'records' : records
    }
    return render(request, 'politicians/politician_view.html', context)

# Add a politician (together with a politician record).
def politician_add(request):
    if request.method == "GET":
        pf = PoliticianForm()
        rf = PoliticianRecordForm()
    elif request.method == "POST":
        pf = PoliticianForm(request.POST)
        rf = PoliticianRecordForm(request.POST)    
        if pf.is_valid() and rf.is_valid():
            # Get the politician, or create if they do not exist.
            first_name = pf.cleaned_data['first_name']
            middle_name = pf.cleaned_data['middle_name']
            last_name = pf.cleaned_data['last_name']
            politician, _ = Politician.objects.get_or_create(
                slug = custom_slugify(first_name, middle_name, last_name),
                defaults = {
                    "first_name" : first_name, "middle_name" : middle_name, "last_name" : last_name
                }
            )
            # Check for validity of region and province pairing before saving the record.
            region = rf.cleaned_data['region']
            province = rf.cleaned_data['province']
            if province not in region.province_set.all():
                messages.error(request, f"{province.name} and {region.name} are an invalid pair. Please try again.")
            else:
                record = rf.save(commit = False)
                record.politician = politician
                record.save()
                return redirect('politicians:politician_view', slug = politician.slug)
    context = {
        'politician_form' : pf,
        'record_form' : rf,
    }
    return render(request, 'politicians/politician_add.html', context)

# Add a politician record.
def politicianrecord_add(request, slug):
    politician = Politician.objects.get(slug = slug)
    if request.method == "GET":
        rf = PoliticianRecordForm()
    elif request.method == "POST":
        rf = PoliticianRecordForm(request.POST)
        if rf.is_valid():
            record = rf.save(commit = False)
            record.politician = politician
            record.save()
            return redirect('politicians:politician_view', slug = slug)
    context = {
        'politician' : politician,
        'record_form' : rf,
    }
    return render(request, 'politicians/politician_add.html', context)

# Update a politician.
def politician_update(request, slug):
    politician = Politician.objects.get(slug = slug)
    if request.method == "GET":
        pf = PoliticianForm(instance = politician)
    elif request.method == "POST":
        pf = PoliticianForm(request.POST, instance = politician)
        if pf.is_valid():
            new_slug = custom_slugify(
                pf.cleaned_data["first_name"],
                pf.cleaned_data["middle_name"],
                pf.cleaned_data["last_name"]
            )
            duplicate = Politician.objects.filter(slug = new_slug).exclude(id = politician.id).exists()
            if duplicate:
                politician = Politician.objects.get(slug = slug)
                messages.error(request, "A politician with that name already exists.")
            else:
                pf.save()
                return redirect("politicians:politician_view", slug = politician.slug)
    context = {
        'politician' : politician,
        'politician_form' : pf
    }
    return render(request, 'politicians/politician_update.html', context)

# Update a politician record.
def politicianrecord_update(request, slug, record_id):
    politician = Politician.objects.get(slug = slug)
    record = get_object_or_404(PoliticianRecord, id = record_id)
    if politician != record.politician:
        context = {
            "politician" : politician,
            "record" : record,
            "action_name" : "Update"
        }
        return render(request, 'politicians/politicianrecord_invalid.html', context)
    else:
        if request.method == "GET":
            rf = PoliticianRecordForm(instance = record)
        elif request.method == "POST":
            rf = PoliticianRecordForm(request.POST, instance = record)
            if rf.is_valid():
                # Check for validity of region and province pairing before saving the record.
                region = rf.cleaned_data['region']
                province = rf.cleaned_data['province']
                if province not in region.province_set.all():
                    messages.error(request, f"{province.name} and {region.name} are an invalid pair. Please try again.")
                else:
                    rf.save()
                    return redirect('politicians:politician_view', slug = slug)
        context = {
            'politician' : politician,
            'record' : record,
            'record_form' : rf
        }
        return render(request, 'politicians/politicianrecord_update.html', context)

# Delete a politician record.
def politicianrecord_delete(request, slug, record_id):
    politician = Politician.objects.get(slug = slug)
    record = get_object_or_404(PoliticianRecord, id = record_id)
    if politician != record.politician:
        context = {
            "politician" : politician,
            "record" : record,
            "action_name" : "Delete"
        }
        return render(request, 'politicians/politicianrecord_invalid.html', context)
    else:
        one_record_left = PoliticianRecord.objects.filter(politician = politician).count() == 1
        if request.method == "GET":
            context = {
                'politician' : politician,
                'record' : record,
                'one_record_left' : one_record_left
            }
            return render(request, "politicians/politicianrecord_delete.html", context)
        elif request.method == "POST":
            if one_record_left:
                # Note that both the record and the politician are deleted due to on_delete = models.CASCADE.
                # record.delete()
                politician.delete()
                return redirect("politicians:index")
            else:
                record.delete()
                # Index page for now, can be overview page later
                return redirect("politicians:politician_view", slug = politician.slug)
