from django.shortcuts import render
from politicians.models import Politician, PoliticianRecord, Province, Region

def dashboard(request):
    """Main dashboard view with overview statistics and navigation"""
    
    # Basic statistics only
    total_politicians = Politician.objects.count()
    total_records = PoliticianRecord.objects.count()
    total_provinces = Province.objects.count()
    total_regions = Region.objects.count()
    
    # Year range
    years = PoliticianRecord.objects.values_list('year', flat=True).distinct().order_by('year')
    year_range = f"{min(years)} - {max(years)}" if years else "No data"
    
    context = {
        'total_politicians': total_politicians,
        'total_records': total_records,
        'total_provinces': total_provinces,
        'total_regions': total_regions,
        'year_range': year_range,
    }
    
    return render(request, 'overview/dashboard.html', context)
