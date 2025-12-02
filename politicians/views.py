from django.shortcuts import render, redirect, get_object_or_404
from .models import custom_slugify, Politician, PoliticianRecord, Province
from .forms import PoliticianForm, PoliticianRecordForm
from django.http import HttpResponse
from django.contrib import messages
from django.db.models import Q
import numpy as np
from django.utils.text import slugify
from .graph import *  
import os
from django.conf import settings
import json
from django.templatetags.static import static

# Create your views here.

# Landing page
def index(request):
    politicians = Politician.objects.all()
    
    # Get search query if provided
    search_query = request.GET.get('search', '')
    if search_query:
        politicians = politicians.filter(
            Q(first_name__icontains=search_query) |
            Q(middle_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    # Paginate results
    politicians = politicians.order_by('first_name', 'last_name')[:50]  # Limit to 50 for performance
    total_count = politicians.count()
    context = {
        'politicians': politicians,
        'total_count': total_count,
        'search_query': search_query,
    }
    return render(request, 'politicians/politician_list.html', context)

# View a specific politician's details and records.
def politician_view(request, slug):
    # Extract the politician and their records.
    politician = Politician.objects.get(slug = slug)
    records = PoliticianRecord.objects.filter(politician = politician)

    # Extract extra information for featured politicians based on JSON files
    featured_politician_slugs = ["francisco-moreno-domagoso", "ma_josefina-go-belmonte", "datu_andal-uy-ampatuan", "stephany-uy-tan", "ma_theresa-bonoan_david"]
    if slug in featured_politician_slugs:
        json_path = os.path.join(settings.BASE_DIR, f"politicians/json_data/{slug}.json")
        with open(json_path, "r", encoding = "utf-8") as f:
            extra_info = json.load(f)
    else:
        extra_info = {}
    context = {
        'politician': politician,
        'records' : records,
        'extra_info' : extra_info
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

def get_base_context(request):
    provinces = list(Province.objects.order_by("name").values_list("name", flat = True))
    years = [2004, 2007, 2010, 2013, 2016, 2019, 2022]
    selected_province = request.GET.get("province", provinces[0] if provinces else None)
    selected_year = int(request.GET.get("year", years[-1] if years else 2022))
    return {
        "provinces": provinces,
        "years": years,
        "selected_province": selected_province,
        "selected_year": selected_year,
    }
     
def plot_graph(request):
    context = get_base_context(request)
    province = context['selected_province']
    year = context['selected_year']
    degree_threshold = 2

    am_df, unique_records, name_data = generate_adjacency_matrix(province, year)
    G_filtered, above_threshold, above_threshold_community, communities = generate_graph(am_df, unique_records, name_data, degree_threshold)
    static_graph, pos = display_static_graph(province, year, degree_threshold, G_filtered, above_threshold, communities)
    interactive_html = get_interactive_html(degree_threshold, above_threshold, communities, G_filtered, pos)
    context.update({
        "static_graph" : static_graph,
        "interactive_html" : interactive_html
    })
    return render(request, 'politicians/graph_template.html', context)

