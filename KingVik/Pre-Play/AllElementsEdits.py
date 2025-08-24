import requests
import pandas as pd
import geopandas as gpd
from datetime import datetime, timedelta, UTC
import os

# Load African countries
url = "https://naturalearth.s3.amazonaws.com/110m_cultural/ne_110m_admin_0_countries.zip"
print("Loading African countries...")
world = gpd.read_file(url)
africa = world[world['CONTINENT'] == 'Africa'][['NAME', 'geometry']]

output_dir = r"C:\Users\chukw\OneDrive\Documentos\TomTom Event"
os.makedirs(output_dir, exist_ok=True)
csv_path = os.path.join(output_dir, "AllElementsEdits.csv")

# Set start date
if os.path.exists(csv_path):
    existing_df = pd.read_csv(csv_path, parse_dates=["date"])
    last_date = existing_df["date"].max().date()
    print(f"Existing file found, last date in data: {last_date}")
    start_date = last_date + timedelta(days=1)
else:
    print("No existing file, starting from 13/06/2023")
    start_date = datetime(2025, 6, 13).date()

end_date = datetime.now(UTC).date()

if start_date > end_date:
    print("Data already up-to-date. No new data to download.")
    exit()

overpass_url = "https://overpass-api.de/api/interpreter"
all_records = []

for single_date in (start_date + timedelta(n) for n in range((end_date - start_date).days)):
    next_date = single_date + timedelta(days=1)
    date_filter = f"{single_date.strftime('%Y-%m-%dT00:00:00Z')},{next_date.strftime('%Y-%m-%dT00:00:00Z')}"
    print(f"\n📅 Processing date: {single_date}")

    day_record_count = 0

    for idx, row in africa.iterrows():
        country = row['NAME']
        minlon, minlat, maxlon, maxlat = row['geometry'].bounds

        print(f"➡️  Processing {country} on {single_date}...")

        query = f"""
        [out:json][timeout:3600];
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
                    length = len(geometry) * 0.01  # simple length estimate

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
                    stats["building"] +
                    stats["highway_km"] +
                    stats["landuse_km2"] +
                    stats["waterway_km"]
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

            day_record_count += count_per_country
            print(f"✅ Completed {country}: {count_per_country} user records")

        except Exception as e:
            print(f"❌ Error processing {country} on {single_date}: {e}")

    print(f"\n✅ Completed {single_date}, total records: {day_record_count}")

if all_records:
    df_new = pd.DataFrame(all_records)
    if os.path.exists(csv_path):
        df_combined = pd.concat([existing_df, df_new], ignore_index=True)
        df_combined.to_csv(csv_path, index=False)
        print(f"\n✅ Updated {csv_path} with {len(df_new)} new records.")
    else:
        df_new.to_csv(csv_path, index=False)
        print(f"\n✅ Created {csv_path} with {len(df_new)} records.")
else:
    print("⚠️ No new data collected.")
