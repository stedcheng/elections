from politicians.models import *
import pandas as pd
from django.utils.text import slugify

df_region_province = pd.read_csv("datasets/region_province.csv")
df_politicians = pd.read_csv("datasets/politicians.csv")
df_political_dynasty = pd.read_csv("datasets/political_dynasty_v9.csv")

def normalize_entry(entry):
    if pd.isna(entry) or entry in (None, "", " ", ".", "N/A"):
        return None   # store as actual NULL in DB
    return str(entry).strip()

# Regions table
regions = df_region_province["Region"].unique()
for region in regions:
    region_object, _ = Region.objects.get_or_create(name = region)
print("Number of region objects saved:", Region.objects.count())
print(Region.objects.all())

# Provinces table
for i in range(df_region_province.shape[0]):
    row = df_region_province.iloc[i]
    region, province = row["Region"], row["Province"]
    region_object, _ = Region.objects.get_or_create(name = region)
    province_object, _ = Province.objects.get_or_create(name = province, region = region_object)
print("Number of province objects saved:", Province.objects.count())
print(Province.objects.all())

# Confirmation
for region in Region.objects.all():
    for province in region.province_set.all():
        print(region.name, "->", province.name)

# Politicians table 
politician_objects = []
def custom_slugify(first_name, middle_name, last_name):
    if middle_name is None:
        middle_name = ""
    full_name = " ".join([p for p in [
        first_name.strip().replace(" ", "_"),
        middle_name.strip().replace(" ", "_"),
        last_name.strip().replace(" ", "_"),
    ] if p])
    return slugify(full_name)

for _, row in df_politicians.iterrows():
    first_name = row["First Name"]
    middle_name = normalize_entry(row["Middle Name"])
    last_name = row["Last Name"]
    slug = custom_slugify(first_name, middle_name, last_name)
    politician_objects.append(Politician(
        first_name = first_name, middle_name = middle_name, last_name = last_name, slug = slug
    ))
from collections import Counter

dupe_counts = Counter([p.slug for p in politician_objects])
duplicates = [s for s, c in dupe_counts.items() if c > 1]
print("Duplicate slugs in batch:", duplicates)

empties = [p for p in politician_objects if not p.slug]
print("Empty slugs:", [f"{p.first_name} {p.middle_name} {p.last_name}" for p in empties])

Politician.objects.bulk_create(politician_objects, batch_size = 1000)
print("Number of politician objects saved:", Politician.objects.count())

# Politician records table
politician_map = {
    (p.first_name, normalize_entry(p.middle_name), p.last_name) : p
    for p in Politician.objects.all()
}
region_map = {r.name : r for r in Region.objects.all()}
province_map = {p.name : p for p in Province.objects.all()}

politician_record_objects = []
for _, row in df_political_dynasty.iterrows():
    pol_key = (
        row["First Name"],
        normalize_entry(row["Middle Name"]),
        row["Last Name"]
    )
    politician_record_objects.append(PoliticianRecord(
        politician = politician_map[pol_key],
        region = region_map.get(row["Region"], None),
        province = province_map[row["Province"]],
        position = row["Position"],
        party = row["Party"],
        year = row["Year"],
        community = row["Community"]
    ))
PoliticianRecord.objects.bulk_create(politician_record_objects, batch_size = 1000)
print("Number of politician record objects saved:", PoliticianRecord.objects.count())

