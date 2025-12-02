import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import networkx as nx
from pyvis.network import Network
from django.db.models import Min

from .models import PoliticianRecord
import io
import base64

def get_colors(degree_threshold, largest_community, G_filtered, above_threshold):
    if degree_threshold <= 1:
        node_color_map = {
            node : (
                "#ee734a" if node in largest_community else
                "#777777"
            )
            for node in G_filtered.nodes()
        }
        legend_items = [
            patches.Patch(color = "#e56249", label = "Largest Dynasty"),
            patches.Patch(color = "#777777", label = "Other")
        ]
    else:
        node_color_map = {
            node : (
                "#d54a46" if node in largest_community and node in above_threshold else
                "#ee734a" if node in largest_community else
                "#fba050" if node in above_threshold else
                "#777777"
            )
            for node in G_filtered.nodes()
        }
        legend_items = [
            patches.Patch(color = "#ee734a", label = "Largest Dynasty"),
            patches.Patch(color = "#fba050", label = f"At Least {degree_threshold} Connections"),
            patches.Patch(color = "#d54a46", label = "Both"),
            patches.Patch(color = "#777777", label = "Neither")
        ]
    return node_color_map, legend_items

def generate_adjacency_matrix(province, year): 
    first_ids = (
        PoliticianRecord.objects
        .filter(province__name = province, year = year)
        .values("politician")
        .annotate(first_id = Min("id"))
        .values_list("first_id", flat = True)
    )
    unique_records = PoliticianRecord.objects.filter(id__in = first_ids)

    name_data = {
        record.politician.slug: {
            "Last Name": record.politician.last_name,
            "Middle Name": record.politician.middle_name,
            "Position Weight": record.position_weight(),
            "Community": record.community,
            "Position": record.position
        }
        for record in unique_records
    }

    names = [record.politician.slug for record in unique_records]
    num_names = len(unique_records)
    am = np.zeros((num_names, num_names), dtype = int)
    ln = [record.politician.last_name for record in unique_records]
    mn = [record.politician.middle_name for record in unique_records]
    weights = [record.position_weight() for record in unique_records]

    for i in range(num_names):
        for j in range(i + 1, num_names):
            # Consanguinity conditions
            if ln[i] == ln[j] and mn[i] == mn[j]:  # Consanguinity 1
                weight = weights[i] * weights[j]
            elif ln[i] == ln[j] and mn[i] != mn[j]:  # Consanguinity 2
                weight = (weights[i] * weights[j]) * 3 / 4
            elif mn[i] != "" and (ln[i] == mn[j] or mn[i] == ln[j]):  # Consanguinity 3+
                weight = (weights[i] * weights[j]) * 2 / 4
            elif mn[i] == mn[j] and mn[i] != "":
                weight = (weights[i] * weights[j]) * 1 / 4
            else:
                weight = 0

            am[i, j] = weight
            am[j, i] = weight  # Ensure symmetry

    # Create a graph with all politicians using the original adjacency matrix
    am_df = pd.DataFrame(am, index = names, columns = names)
    return am_df, unique_records, name_data

def generate_graph(am_df, unique_records, name_data, degree_threshold):
    # Include only those politicians whose degree is higher than the degree threshold...
    nonzero_counts = pd.DataFrame((am_df > 0).sum(axis = 1))
    above_threshold = list(nonzero_counts[nonzero_counts[0] >= degree_threshold].index)

    # ...and the politicians who are connected to those higher than the degree threshold
    above_threshold_community = set()
    communities = []
    unique_communities = unique_records.values_list("community", flat = True).distinct()
    for comm in unique_communities:
        slugs = unique_records.filter(community = comm).values_list("politician__slug", flat = True)
        communities.append(list(slugs))
    for comm in communities:
        if any(n in comm for n in above_threshold):
            above_threshold_community.update(comm)
    above_threshold_community = list(above_threshold_community)
    
    # Create a graph with only politicians from the above two categories
    am_df_filtered = am_df[above_threshold_community].loc[above_threshold_community]    
    G_filtered = nx.from_pandas_adjacency(am_df_filtered)

    # Add "Position Weight" as a node attribute
    for name in G_filtered.nodes:
        G_filtered.nodes[name]["Position Weight"] = name_data[name]["Position Weight"]
        G_filtered.nodes[name]["Community"] = name_data[name]["Community"]
        G_filtered.nodes[name]["Position"] = name_data[name]["Position"]

    return G_filtered, above_threshold, above_threshold_community, communities

def display_static_graph(province, year, degree_threshold, G_filtered, above_threshold, communities):
    # Prepare colors for plotting
    sorted_communities = sorted(communities, key = len, reverse = True)
    if len(sorted_communities) >= 1 and len(above_threshold) >= 1:
        largest_community = sorted_communities[0]
        node_color_map, legend_items = get_colors(degree_threshold, largest_community, G_filtered, above_threshold)
        
        # Create the static graph 
        fig, ax = plt.subplots(figsize = (20, 15))
        pos = nx.spring_layout(G_filtered, k = 0.5, iterations = 100)
        nx.draw(G_filtered, pos,
                node_color = [node_color_map[node] for node in G_filtered.nodes()],
                width = [G_filtered[u][v]["weight"] for u, v in G_filtered.edges()])
        ax.set_title(f"Political Network of {province} ({year})")
        ax.legend(handles = legend_items, title = "Politician Category", loc = "best")

        # Save the static graph
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight")
        buf.seek(0)
        static_graph = base64.b64encode(buf.read()).decode("utf-8")
        buf.close()
        return static_graph, pos

def get_interactive_html(degree_threshold, above_threshold, communities, G_filtered, pos):
    # Prepare colors for plotting
    sorted_communities = sorted(communities, key = len, reverse = True)
    if len(sorted_communities) >= 1 and len(above_threshold) >= 1:
        largest_community = sorted_communities[0]
        node_color_map, _ = get_colors(degree_threshold, largest_community, G_filtered, above_threshold)
            
        # Create the interactive graph
        net = Network(width = "100%", notebook = False)
        net.toggle_physics(False)
        for node in G_filtered.nodes():
            net.add_node(node, label = " ", x = 500*pos[node][0], y = -500*pos[node][1], title = node,
                        color = node_color_map[node], physics = True)
        for u, v in G_filtered.edges():
            net.add_edge(u, v, width = G_filtered[u][v].get("weight"), color = "black")
        interactive_html = net.generate_html()
        return interactive_html