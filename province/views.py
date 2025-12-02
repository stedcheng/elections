from django.shortcuts import render
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from plotly.utils import PlotlyJSONEncoder
import os
from django.conf import settings
from django.shortcuts import render
from politicians.models import Province, Politician, PoliticianRecord
import json

# Get the base context using the models we had
def get_base_context(request):
    """Get common context data for all views using the ORM"""

    # 1. Get all provinces from the DB
    provinces = list(
        Province.objects.order_by("name").values_list("name", flat=True)
    )

    # 2. Get distinct years from PoliticianRecord (sorted)
    years = list(
        PoliticianRecord.objects.order_by("year")
        .values_list("year", flat=True)
        .distinct()
    )

    # If DB has no years yet (fresh DB), fall back
    if not years:
        years = [2004, 2007, 2010, 2013, 2016, 2019, 2022]

    # 3. Handle selected province + selected year
    selected_province = request.GET.get("province", provinces[0] if provinces else None)
    selected_year = int(request.GET.get("year", years[-1] if years else 2022))

    return {
        "provinces": provinces,
        "years": years,
        "selected_province": selected_province,
        "selected_year": selected_year,
    }

#Extract the name of politicians
def family_names(politician: Politician):
    """Extract family names from a Politician model instance"""
    middle = politician.middle_name
    last = politician.last_name

    family_names = []

    # Case 1: Middle name == Last name (and last is not null)
    if middle and last and middle == last:
        family_names.append([last, "Both"])
    else:
        # Case 2: Middle name exists
        if middle:
            family_names.append([middle, "Middle"])
        # Case 3: Last name always included if present
        if last:
            family_names.append([last, "Last"])

    return family_names

def create_dynasty_size_chart(province_name, year):
    """
    Create dynasty size chart using Django ORM,
    excluding communities with size 1 or no valid family names.
    """

    # 1. Filter records by province + year
    records = (
        PoliticianRecord.objects
        .select_related("politician", "province")
        .filter(province__name=province_name, year=year)
    )

    if not records.exists():
        return None, f"No political records found for {province_name} ({year})."

    # 2. Group into communities
    communities = {}
    for rec in records:
        cid = rec.community
        if cid not in communities:
            communities[cid] = []
        communities[cid].append(rec)

    community_size = {cid: len(members) for cid, members in communities.items()}

    # 3. FAMILY NAMES per politician
    name_mentions = []
    for cid, members in communities.items():
        for rec in members:
            fnames = family_names(rec.politician)
            for fam, source in fnames:
                # ignore invalid family names
                if fam is None or str(fam).strip().lower() == "nan":
                    continue
                name_mentions.append({
                    "community": cid,
                    "family_name": fam,
                    "source": source,
                })

    # 4. COUNT name mentions per community
    counts = {}
    for row in name_mentions:
        key = (row["community"], row["family_name"])
        counts[key] = counts.get(key, 0) + 1

    # 4a. Only include family names with total count >= 3
    family_totals = {}
    for (cid, fam), count in counts.items():
        family_totals[(cid, fam)] = family_totals.get((cid, fam), 0) + count

    counts = {k: v for k, v in counts.items() if family_totals[k] >= 3}

    # 5. Compute proportions and greatest contributor per community
    greatest = {}
    for (cid, fam), count in counts.items():
        size = community_size[cid]
        proportion = count / size

        if cid not in greatest or proportion > greatest[cid]["proportion"]:
            greatest[cid] = {
                "family_name": fam,
                "proportion": proportion
            }

    # 6. FINAL LIST for chart, only keep communities with size>1 and valid greatest
    display_list = []
    for cid, size in community_size.items():
        if size <= 1:
            continue  # skip single-member communities
        g = greatest.get(cid)
        if g is None:
            continue  # skip if no valid family names
        display_list.append({
            "community": cid,
            "size": size,
            "greatest": f"{g['proportion']:.2%} | {g['family_name'].title()}"
        })

    if not display_list:
        return None, f"No valid dynasties to display in {province_name} ({year})."

    # Sort by community ID
    display_list = sorted(display_list, key=lambda x: x["community"])

    # 7. CREATE PLOTLY GRAPH
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[row["community"] for row in display_list],
        y=[row["size"] for row in display_list],
        customdata=[row["greatest"] for row in display_list],
        hovertemplate=(
            "Community: %{x}<br>"
            "Size: %{y}<br>"
            "Greatest Family Name: %{customdata}"
            "<extra></extra>"
        ),
        marker_color="#fa904d"
    ))

    fig.update_layout(
        title=f"Sizes of the Dynasties in {province_name} ({year})",
        xaxis_title="Community ID",
        yaxis_title="Size",
        height=400
    )

    return json.dumps(fig, cls=PlotlyJSONEncoder), None

def get_top_family_name(province_name, year):
    """
    Return the top 1 most frequent family name in the largest dynasty,
    along with the list of politicians having that family name.
    """
    # 1. Fetch records
    records = (
        PoliticianRecord.objects
        .select_related("politician", "province")
        .filter(province__name=province_name, year=year)
    )

    if not records.exists():
        return None, f"No records found for {province_name} ({year})."

    # 2. Group by community
    communities = {}
    for rec in records:
        cid = rec.community
        communities.setdefault(cid, []).append(rec)

    if not communities:
        return None, f"No dynasties found for {province_name} ({year})."

    # 3. Identify largest dynasty
    largest_community_id = max(communities, key=lambda cid: len(communities[cid]))
    largest_dynasty = communities[largest_community_id]

    # 4. Collect valid family names
    family_list = []
    family_to_politicians = {}  # map family -> list of politician names
    for rec in largest_dynasty:
        fnames = family_names(rec.politician)
        for fam, _ in fnames:
            if fam and str(fam).strip().lower() != "nan":
                fam_clean = fam.strip()
                family_list.append(fam_clean)
                family_to_politicians.setdefault(fam_clean, []).append(rec.politician)

    if not family_list:
        return None, f"No family name data for largest dynasty in {province_name} ({year})."

    # 5. Count occurrences
    df = pd.DataFrame({'Family': family_list})
    top_family = df['Family'].value_counts().idxmax()
    top_count = int(df['Family'].value_counts().max())

    # 6. Get politicians with the top family name
    top_family_politicians = family_to_politicians.get(top_family, [])

    dct = {
        'Family': top_family,
        'Count': top_count,
        'Politicians': top_family_politicians
    }
    return dct, None

def province_analysis(request):
    # 1. Get common context data
    context = get_base_context(request)
    
    province = context['selected_province']
    year = context['selected_year']

    # 2. Create charts using ORM-based functions
    dynasty_chart, dynasty_warning = create_dynasty_size_chart(province, year)
    top_family_dict, top_family_warning = get_top_family_name(province, year)

    # 3. Create concentration scatter plot
    concentration_chart = None
    concentration_warning = None

    # Fetch all records for this province and year
    records = (
        PoliticianRecord.objects
        .select_related("politician", "province")
        .filter(province__name=province, year=year)
    )

    if records.exists():
        # Group by community
        communities = {}
        for rec in records:
            cid = rec.community   # MUST EXIST: community field
            communities.setdefault(cid, []).append(rec)

        # Filter dynasties with size > 1
        dynasties = {cid: members for cid, members in communities.items() if len(members) > 1}

        if dynasties:
            # Compute family name concentration and average position weight
            plot_data = []

            for cid, members in dynasties.items():
                # 1. Community size
                size = len(members)

                # 2. Count family name mentions
                name_mentions = []
                for rec in members:
                    fnames = family_names(rec.politician)
                    for fam, source in fnames:
                        name_mentions.append({"family_name": fam, "source": source})

                if not name_mentions:
                    continue

                # 3. Compute proportion per family
                counts = {}
                for nm in name_mentions:
                    counts[nm["family_name"]] = counts.get(nm["family_name"], 0) + 1
                dominant_family = max(counts, key=counts.get)
                max_prop = counts[dominant_family] / size

                # 4. Average position weight
                avg_position_weight = sum(rec.position_weight() for rec in members) / size

                plot_data.append({
                    "Community": cid,
                    "Family": dominant_family,
                    "Size": size,
                    "Proportion": max_prop,
                    "Average Position Weight": avg_position_weight
                })

            if plot_data:
                # Create Plotly scatter plot
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=[d["Proportion"] for d in plot_data],
                    y=[d["Average Position Weight"] for d in plot_data],
                    mode='markers',
                    marker=dict(
                        size=[d["Size"] * 10 for d in plot_data],
                        color=[d["Size"] for d in plot_data],
                        colorscale='Viridis',
                        showscale=True,
                        opacity=0.75
                    ),
                    customdata=[[d['Community'], d['Family']] for d in plot_data],
                    hovertemplate=(
                        'Community: %{customdata[0]}<br>'
                        'Dominant Family: %{customdata[1]}<br>'
                        'Concentration: %{x:.2%}<br>'
                        'Avg Position Weight: %{y:.2f}<br>'
                        'Size: %{marker.color}<extra></extra>'
                    )
                ))

                fig.update_layout(
                    title='Family Name Concentration vs Dynasty Size and Average Position Weights',
                    xaxis_title='Family Name Concentration',
                    yaxis_title='Average Position Weight',
                    height=400
                )

                concentration_chart = json.dumps(fig, cls=PlotlyJSONEncoder)
            else:
                concentration_warning = f"No family name data found for dynasties in {province} ({year})."
        else:
            concentration_warning = f"No dynasties found in {province} ({year})."
    else:
        concentration_warning = f"No political records found for {province} ({year})."

    # 4. Update context for template
    context.update({
        'dynasty_chart': dynasty_chart,
        'dynasty_warning': dynasty_warning,
        'top_family': top_family_dict,
        'top_family_warning': top_family_warning,
        'concentration_chart': concentration_chart,
        'concentration_warning': concentration_warning
    })

    return render(request, 'province/province_analysis.html', context)