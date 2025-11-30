from django.shortcuts import render
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from plotly.utils import PlotlyJSONEncoder
import os
from django.conf import settings
from django.shortcuts import render
from .models import Province, Politician, Region, PoliticianRecord
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

# Generate a template of the size chart
def create_dynasty_size_chart(province_name, year):
    """
    Create dynasty size chart using Django ORM.
    Equivalent to the pandas version.
    """

    # 1. Filter records by province + year
    records = (
        PoliticianRecord.objects
        .select_related("politician", "province")
        .filter(province__name=province_name, year=year)
    )

    if not records.exists():
        return None, f"No political records found for {province_name} ({year})."

    # 2. Group into communities (dynasties)
    # Expecting: record.community (int or string)
    communities = {}
    for rec in records:
        cid = rec.community  # YOU MUST CONFIRM THIS FIELD EXISTS
        if cid not in communities:
            communities[cid] = []
        communities[cid].append(rec)

    # COMMUNITY SIZE DICT → {community_id: size}
    community_size = {cid: len(members) for cid, members in communities.items()}

    # If all sizes are 1 → no dynasty
    if not community_size or (
        min(community_size.values()) == 1 and max(community_size.values()) == 1
    ):
        return None, f"There were no dynasties in {province_name} ({year})."

    # 3. FAMILY NAMES per politician (using ORM-based family_names function)
    name_mentions = []  # rows: {"community": X, "family_name": Y}

    for cid, members in communities.items():
        for rec in members:
            fnames = family_names(rec.politician)
            for fam, source in fnames:
                name_mentions.append({
                    "community": cid,
                    "family_name": fam,
                    "source": source,
                })

    # 4. COUNT name mentions PER community
    # dict: {(community, family_name): count}
    counts = {}
    for row in name_mentions:
        key = (row["community"], row["family_name"])
        counts[key] = counts.get(key, 0) + 1

    # 5. Compute proportions and greatest contributor per community
    # dict: {community: {"family_name": X, "proportion": p}}
    greatest = {}
    for (cid, fam), count in counts.items():
        size = community_size[cid]
        proportion = count / size

        if cid not in greatest or proportion > greatest[cid]["proportion"]:
            greatest[cid] = {
                "family_name": fam,
                "proportion": proportion
            }

    # 6. FINAL LIST for chart
    display_list = []
    for cid, size in community_size.items():
        g = greatest[cid]
        display_list.append({
            "community": cid,
            "size": size,
            "greatest": f"{g['proportion']:.2%} | {g['family_name'].title()}"
        })

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

# Generate distribution per family
def create_family_name_distribution_chart(province_name, year):
    """Create family name distribution chart for the largest dynasty using ORM"""

    # 1. Fetch records for province + year
    records = (
        PoliticianRecord.objects
        .select_related("politician", "province")
        .filter(province__name=province_name, year=year)
    )

    if not records.exists():
        return None, f"No data available for {province_name} ({year})."

    # 2. Group by community
    communities = {}
    for rec in records:
        cid = rec.community            # IMPORTANT: must exist
        communities.setdefault(cid, []).append(rec)

    if not communities:
        return None, f"No dynasties found for {province_name} ({year})."

    # 3. Identify the LARGEST dynasty
    largest_community_id = max(communities, key=lambda cid: len(communities[cid]))
    largest_dynasty = communities[largest_community_id]

    # 4. Extract family names for each member
    name_mentions = []  # [{"family_name": X, "source": Y}]

    for rec in largest_dynasty:
        fnames = family_names(rec.politician)     # [["Garcia", "Last"], ...]
        for fam, source in fnames:
            name_mentions.append({
                "family_name": fam,
                "source": source
            })

    if not name_mentions:
        return None, f"No family name data for largest dynasty in {province_name} ({year})."

    # 5. Count mentions → {(family_name, source): count}
    combo_counts = {}
    for nm in name_mentions:
        key = (nm["family_name"], nm["source"])
        combo_counts[key] = combo_counts.get(key, 0) + 1

    # 6. Total counts per family → {family_name: total_count}
    family_totals = {}
    for (fam, _), c in combo_counts.items():
        family_totals[fam] = family_totals.get(fam, 0) + c

    # 7. Group small families into "Others" IF >= 5 families
    unique_families = list(family_totals.keys())
    group_is_needed = len(unique_families) >= 5

    # Build table for the chart
    rows = []  # [{"group": X, "source": Y, "count": Z}]

    for (fam, source), count in combo_counts.items():
        if group_is_needed and family_totals[fam] <= 1:
            group = "Others"
        else:
            group = fam

        rows.append({
            "group": group,
            "source": source,
            "count": count
        })

    # 8. Aggregate again by (group, source)
    final_counts = {}
    for row in rows:
        key = (row["group"], row["source"])
        final_counts[key] = final_counts.get(key, 0) + row["count"]

    final_rows = []
    for (group, source), count in final_counts.items():
        final_rows.append({
            "Group": group,
            "Source": source,
            "Count": count,
        })

    # 9. Create Plotly chart (horizontal bar)
    fig = px.bar(
        final_rows,
        x="Count",
        y="Group",
        color="Source",
        orientation="h",
        color_discrete_map={'Last': '#d54a46', 'Middle': '#fba050', 'Both': '#ee734a'},
        title="Family Name Distribution of the Largest Dynasty"
    )

    fig.update_layout(height=400, yaxis={"categoryorder": "total ascending"})

    return json.dumps(fig, cls=PlotlyJSONEncoder), None

def province_analysis(request):
    # 1. Get common context data
    context = get_base_context(request)
    
    province = context['selected_province']
    year = context['selected_year']

    # 2. Create charts using ORM-based functions
    dynasty_chart, dynasty_warning = create_dynasty_size_chart(province, year)
    family_chart, family_warning = create_family_name_distribution_chart(province, year)

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
                max_prop = max(counts.values()) / size

                # 4. Average position weight
                avg_position_weight = sum(rec.position_weight() for rec in members) / size

                plot_data.append({
                    "Community": cid,
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
                    customdata=[d["Community"] for d in plot_data],
                    hovertemplate=(
                        'Community: %{customdata}<br>'
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
        'family_chart': family_chart,
        'family_warning': family_warning,
        'concentration_chart': concentration_chart,
        'concentration_warning': concentration_warning
    })

    return render(request, 'province/province_analysis.html', context)