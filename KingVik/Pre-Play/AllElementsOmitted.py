import requests
import pandas as pd
import geopandas as gpd
from datetime import datetime, timedelta, UTC, date
import os

# Load African countries
url = "https://naturalearth.s3.amazonaws.com/110m_cultural/ne_110m_admin_0_countries.zip"
print("Loading African countries...")
world = gpd.read_file(url)
africa = world[world['CONTINENT'] == 'Africa'][['NAME', 'geometry']]

output_dir = r"C:\Users\chukw\OneDrive\Documentos\TomTom Event"
os.makedirs(output_dir, exist_ok=True)
csv_path = os.path.join(output_dir, "AllElementsOmitted.csv")

# Load existing data
if os.path.exists(csv_path):
    existing_df = pd.read_csv(csv_path, parse_dates=["date"])
    print(f"Existing file found, current rows: {len(existing_df)}")
else:
    existing_df = pd.DataFrame()
    print("No existing file, creating new one after download.")

# Define missed countries and dates
missed_data = [
    # ("Nigeria", pd.date_range(date(2025, 6, 13), date(2025, 6, 21))),
    # ("Nigeria", pd.date_range(date(2025, 6, 29), date(2025, 7, 3))),
    # ("Congo", [date(2025, 6, 19)]),
    # ("Libya", [date(2025, 7, 27)]),
    # ("Nigeria", [date(2025, 7, 27)]),
    ("Guinea", [date(2025, 7, 28)]),
    ("Côte d'Ivoire", [date(2025, 7, 28)]),

    # ("S. Sudan", [date(2025, 6, 19)]),
    # ("Tanzania", pd.date_range(date(2025, 6, 28), date(2025, 7, 3))),
    # ("Kenya", pd.date_range(date(2025, 6, 30), date(2025, 7, 2))),
    #("Burundi", [date(2025, 7, 3)]),
    #("Eq. Guinea", [date(2025, 7, 11)]),
    #("Uganda", [date(2025, 7, 11)]),
    #("Chad", [date(2025, 7, 17)]),
    #("Angola", [date(2025, 7, 18)])
]

overpass_url = "https://overpass-api.de/api/interpreter"
all_records = []

# Flatten country-date list
targets = [(country, single_date) for country, dates in missed_data for single_date in dates]

for country, single_date in targets:
    next_date = single_date + timedelta(days=1)
    date_filter = f"{single_date.strftime('%Y-%m-%dT00:00:00Z')},{next_date.strftime('%Y-%m-%dT00:00:00Z')}"
    print(f"\n📅 Processing {country} on {single_date}")

    matched_row = africa[africa['NAME'] == country]
    if matched_row.empty:
        print(f"❌ Skipping {country}, boundary not found in shapefile.")
        continue

    minlon, minlat, maxlon, maxlat = matched_row.iloc[0]['geometry'].bounds

    query = f"""
    [out:json][timeout:1200];
    (
      node({minlat},{minlon},{maxlat},{maxlon})(changed:"{date_filter}");
      way({minlat},{minlon},{maxlat},{maxlon})(changed:"{date_filter}");
      relation({minlat},{minlon},{maxlat},{maxlon})(changed:"{date_filter}");
    );
    out meta geom;
    """

    try:
        response = requests.post(overpass_url, data=query)
        response.raise_for_status()
        data = response.json()

        user_stats = {}

        for elem in data.get("elements", []):
            user = elem.get("user")
            version = elem.get("version")
            tags = elem.get("tags", {})
            geometry = elem.get("geometry", [])
            elem_type = elem.get("type")

            if not user:
                continue

            if user not in user_stats:
                user_stats[user] = {
                    "created": 0, "modified": 0, "deleted": 0,
                    "building": 0, "highway_km": 0.0, "landuse_km2": 0.0, "waterway_km": 0.0,
                }

            if elem.get("action") == "delete":
                user_stats[user]["deleted"] += 1
            elif version == 1:
                user_stats[user]["created"] += 1
            else:
                user_stats[user]["modified"] += 1

            if elem_type == "way" and geometry:
                length = len(geometry) * 0.01
                if "building" in tags:
                    user_stats[user]["building"] += 1
                elif "highway" in tags:
                    user_stats[user]["highway_km"] += length
                elif "landuse" in tags:
                    user_stats[user]["landuse_km2"] += length * 0.1
                elif "waterway" in tags:
                    user_stats[user]["waterway_km"] += length

        count_per_country = 0
        for user, stats in user_stats.items():
            total_edits = (
                stats["building"] + stats["highway_km"] +
                stats["landuse_km2"] + stats["waterway_km"]
            )
            total_objects = stats["created"] + stats["modified"] + stats["deleted"]

            all_records.append({
                "user": user,
                "country": country,
                "date": single_date,
                "building": stats["building"],
                "highway (km)": round(stats["highway_km"], 2),
                "landuse (km2)": round(stats["landuse_km2"], 2),
                "waterways (km)": round(stats["waterway_km"], 2),
                "created": stats["created"],
                "modified": stats["modified"],
                "deleted": stats["deleted"],
                "total_edits": round(total_edits, 2),
                "total_objects": total_objects
            })
            count_per_country += 1

        print(f"✅ Completed {country} on {single_date}: {count_per_country} user records")

    except Exception as e:
        print(f"❌ Error processing {country} on {single_date}: {e}")

# Save results
if all_records:
    df_new = pd.DataFrame(all_records)
    if not existing_df.empty:
        combined_df = pd.concat([existing_df, df_new], ignore_index=True)
        combined_df.to_csv(csv_path, index=False)
        print(f"\n✅ Appended {len(df_new)} new records. Total rows now: {len(combined_df)}")
    else:
        df_new.to_csv(csv_path, index=False)
        print(f"\n✅ Created new file with {len(df_new)} records.")
else:
    print("⚠️ No new data collected.")
