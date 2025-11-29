from django.shortcuts import render, redirect, get_object_or_404
from .models import Politician, PoliticianRecord
from .forms import PoliticianForm, PoliticianRecordForm

# Create your views here.

# View a specific politician's details and records.
def politician_view(request, politician_name):
    # URLs are expected to be in "first-middle-last" or "first-last" format.
    name_parts = politician_name.split("-")
    first_name = name_parts[0]
    middle_name = name_parts[1] if len(politician_name.split()) == 3 else ''
    last_name = name_parts[-1]
    # Extract the politician and their records.
    p = get_object_or_404(Politician, first_name = first_name, last_name = last_name, middle_name = middle_name)
    pr = PoliticianRecord.objects.filter(politician = p)
    context = {
        'politician': p,
        'politician_records' : pr
    }
    return render(request, 'politicians/politician_view.html', context)

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
            politician, created = Politician.objects.get_or_create(
                first_name = first_name,
                middle_name = middle_name,
                last_name = last_name
            )

            record = rf.save(commit = False)
            record.politician = politician
            record.save()
            pf.save()
            
            return redirect("politicians:politician_view", politician_name = f"{first_name}-{middle_name}-{last_name}" if middle_name else f"{first_name}-{last_name}")
    context = {
        'politician_form' : pf,
        'record_form' : rf
        }
    return render(request, 'politicians/politician_add.html', context)

def politician_update(request, record_id):
    record = get_object_or_404(PoliticianRecord, id = record_id)
    politician = record.politician
    if request.method == "GET":
        pf = PoliticianForm(instance = politician)
        rf = PoliticianRecordForm(instance = record)
    elif request.method == "POST":
        pf = PoliticianForm(request.POST, instance = politician)
        rf = PoliticianRecordForm(request.POST, instance = record)

        if pf.is_valid() and rf.is_valid():
            pf.save()
            r = rf.save(commit = False)
            r.politician = politician
            r.save()

            return redirect(
                "politician_view",
                politician_name = f"{politician.first_name}-{politician.last_name}"
            )
    context = {
        'politician_form' : pf,
        'record_form' : rf,
        'record' : record
        }
    return render(request, 'politicians/politician_update.html', context)
