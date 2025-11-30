from politicians.models import *
import pandas as pd

# df_region_province = pd.read_csv("datasets/region_province.csv")

# regions = df_region_province["Region"].unique()
# for region in regions:
#     region_object, _ = Region.objects.get_or_create(name = region)

# print(Region.objects.count())
# print(Region.objects.all())

# for i in range(df_region_province.shape[0]):
#     row = df_region_province.iloc[i]
#     region, province = row["Region"], row["Province"]
#     region_object, _ = Region.objects.get_or_create(name = region)
#     province_object, _ = Province.objects.get_or_create(name = province, region = region_object)

# print(Province.objects.count())
# print(Province.objects.all())

# for region in Region.objects.all():
#     for province in region.province_set.all():
#         print(region.name, "->", province.name)

############################## 

df_politicians = pd.read_csv("datasets/politicians.csv")
objs = []
for _, row in df_politicians.iterrows():
    objs.append(Politician(first_name = row["First Name"], middle_name = row["Middle Name"], last_name = row["Last Name"]))
Politician.objects.bulk_create(objs, batch_size = 1000)

print(Politician.objects.count())

##############################

df_political_dynasty = pd.read_csv("datasets/political_dynasty_v9.csv")
def normalize_entry(entry):
    return "" if entry in (None, "", " ", ".", "N/A") else str(entry).strip()

politician_map = {
    (p.first_name, normalize_entry(p.middle_name), p.last_name) : p
    for p in Politician.objects.all()
}
region_map = {r.name : r for r in Region.objects.all()}
province_map = {p.name : p for p in Province.objects.all()}

objs_2 = []
for _, row in df_political_dynasty.iterrows():
    pol_key = (
        row["First Name"],
        normalize_entry(row["Middle Name"]),
        row["Last Name"]
    )
    objs_2.append(PoliticianRecord(
        politician = politician_map[pol_key],
        region = region_map.get(row["Region"], None),
        province = province_map[row["Province"]],
        position = row["Position"],
        party = row["Party"],
        year = row["Year"]
    ))
PoliticianRecord.objects.bulk_create(objs_2, batch_size = 1000)

print(PoliticianRecord.objects.count())

