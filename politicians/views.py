from django.shortcuts import render, redirect
from .models import Politician
from .forms import PoliticianForm

# Create your views here.

def politician_view(request, politician_name):
    first_name = politician_name.split()[0]
    middle_name = politician_name.split()[1] if len(politician_name.split()) == 3 else ''
    last_name = politician_name.split()[-1]
    p = Politician.objects.get(first_name = first_name, last_name = last_name, middle_name = middle_name)
    pr = p.politicianrecord_set.all()
    context = {
        'politician': p,
        'politician_records' : pr
    }
    return render(request, 'politicians/politician_view.html', context)

def politician_add(request):
    if request.method == "GET":
        pf = PoliticianForm()
    elif request.method == "POST":
        pf = PoliticianForm(request.POST)
        if pf.is_valid():
            pf.save()
            return redirect("")
    context = {
        'form' : pf
        }
    return render(request, 'politicians/politician_add.html', context)

def politician_update(request, politician_name):
    first_name = politician_name.split()[0]
    middle_name = politician_name.split()[1] if len(politician_name.split()) == 3 else ''
    last_name = politician_name.split()[-1]
    p = Politician.objects.get(first_name = first_name, last_name = last_name, middle_name = middle_name)
    pr = p.politicianrecord_set.all()
    if request.method == "GET":
        form = PoliticianForm(instance = pr)
    elif request.method == "POST":
        form = PoliticianForm(request.POST, instance = pr)
        if form.is_valid():
            form.save()
            return redirect("")
    context = {
        'form' : form
        }
    return render(request, 'politicians/politician_update.html', context)
