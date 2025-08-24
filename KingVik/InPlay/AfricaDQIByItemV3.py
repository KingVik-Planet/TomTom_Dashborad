import pandas as pd
import requests
import os
import time
from datetime import datetime, date
from io import StringIO

# Configuration and Saving Location
output_dir = r"G:\My Drive\Dashboard\TomTom Power BI\AfricaDQIByItemV3"
os.makedirs(output_dir, exist_ok=True)
execution_date = datetime.now().strftime("%Y-%m-%d")
output_file = os.path.join(output_dir, f"AfricaDQIByItemV3_{execution_date}.csv")

# List of issue types to download
issue_types = {
    "1010": "duplicated node",
    "0"   : "overlapping building",
    "1120": "broken highway continuity",
    "1140": "missing tag or role",
    "1210": "not-connected highway/cycleway",
    "1220": "waterway",
    "1230": "duplicate geometry",
    "1250": "objects intersection",
    "1270": "almost junction",
    "3210": "noexit",
    "5010": "orthograph",
    "4080": "duplicate object",
    "1090": "sudden highway type change"
}

# Country display name mapping
country_display_names = {
    # Subdivisions map to proper country names
    'south_africa': 'South Africa',
    'south_africa_eastern_cape': 'South Africa',
    'south_africa_free_state': 'South Africa',
    'south_africa_gauteng': 'South Africa',
    'south_africa_kwazulu_natal': 'South Africa',
    'south_africa_limpopo': 'South Africa',
    'south_africa_mpumalanga': 'South Africa',
    'south_africa_north_west': 'South Africa',
    'south_africa_northern_cape': 'South Africa',
    'south_africa_western_cape': 'South Africa',
    'south_sudan': 'South Sudan',
    'sao_tome_and_principe': 'Sao Tome and Principe',
    'ivory_coast': 'Ivory Coast',
    'cape_verde': 'Cape Verde',
    'central_african_republic': 'Central African Republic',
    'congo_brazzaville': 'Congo Brazzaville',
    'congo_kinshasa': 'Congo Kinshasa',
    'equatorial_guinea': 'Equatorial Guinea',
    'guinea_bissau': 'Guinea Bissau',
    'burkina_faso': 'Burkina Faso',
    'western_sahara': 'Western Sahara',

    # Nigeria subdivisions
    'nigeria_north_central': 'Nigeria',
    'nigeria_north_east': 'Nigeria',
    'nigeria_north_west': 'Nigeria',
    'nigeria_south_east': 'Nigeria',
    'nigeria_south_south': 'Nigeria',
    'nigeria_south_west': 'Nigeria',

    # Tanzania subdivisions
    'tanzania_coastal': 'Tanzania',
    'tanzania_central': 'Tanzania',
    'tanzania_lake': 'Tanzania',
    'tanzania_northern': 'Tanzania',
    'tanzania_southern_highlands': 'Tanzania',
    'tanzania_west': 'Tanzania',
    'tanzania_zanzibar': 'Tanzania',

    # Mozambique subdivisions
    'mozambique_cabo_delgado': 'Mozambique',
    'mozambique_gaza': 'Mozambique',
    'mozambique_inhambane': 'Mozambique',
    'mozambique_manica': 'Mozambique',
    'mozambique_maputo': 'Mozambique',
    'mozambique_maputo_city': 'Mozambique',
    'mozambique_nampula': 'Mozambique',
    'mozambique_niassa': 'Mozambique',
    'mozambique_sofala': 'Mozambique',
    'mozambique_tete': 'Mozambique',
    'mozambique_zambezia': 'Mozambique',

    # Uganda subdivisions
    'uganda_central': 'Uganda',
    'uganda_eastern': 'Uganda',
    'uganda_northern': 'Uganda',
    'uganda_western': 'Uganda',
}

# Standard African countries list (with underscores)
base_countries = [
    "algeria", "angola", "benin", "botswana", "burkina_faso", "burundi",
    "cape_verde", "cameroon", "central_african_republic", "chad", "comoros",
    "congo_brazzaville", "congo_kinshasa", "djibouti", "egypt", "equatorial_guinea",
    "eritrea", "eswatini", "ethiopia", "gabon", "gambia", "ghana", "guinea",
    "guinea_bissau", "ivory_coast", "kenya", "lesotho", "liberia", "libya",
    "madagascar", "malawi", "mali", "mauritania", "mauritius", "morocco",
    "mozambique", "namibia", "niger", "nigeria", "rwanda", "sao_tome_and_principe",
    "senegal", "seychelles", "sierra_leone", "somalia", "south_africa",
    "south_sudan", "sudan", "tanzania", "togo", "tunisia", "uganda", "zambia", "zimbabwe"
]

# Country configurations with possible subdivisions
country_config = {
    "nigeria": [
        "nigeria", "nigeria_north_central", "nigeria_north_east",
        "nigeria_north_west", "nigeria_south_east",
        "nigeria_south_south", "nigeria_south_west"
    ],
    "tanzania": [
        "tanzania", "tanzania_coastal", "tanzania_central",
        "tanzania_lake", "tanzania_northern", "tanzania_southern_highlands",
        "tanzania_west", "tanzania_zanzibar",
    ],
    "mozambique": [
        "mozambique_cabo_delgado", "mozambique_gaza", "mozambique_inhambane",
        "mozambique_manica", "mozambique_maputo", "mozambique_maputo_city",
        "mozambique_nampula", "mozambique_niassa", "mozambique_sofala",
        "mozambique_tete", "mozambique_zambezia", "mozambique"
    ],
    "south_africa": [
        "south_africa_eastern_cape", "south_africa_free_state", "south_africa_gauteng",
        "south_africa_kwazulu_natal", "south_africa_limpopo", "south_africa_mpumalanga",
        "south_africa_north_west", "south_africa_northern_cape", "south_africa_western_cape", "south_africa"
    ],
    "uganda": [
        "uganda", "uganda_central", "uganda_eastern",
        "uganda_northern", "uganda_western",
    ],
}

# Build complete country list with subdivisions
countries = []
for country in base_countries:
    if country in country_config:
        countries.extend(country_config[country])
    else:
        countries.append(country)

today = date.today().isoformat()
all_data = pd.DataFrame()
max_retries = 3
retry_delay = 5  # seconds

print(f"\n🌍 Starting OSMOSE data collection for {len(countries)} African regions")
print(f"📅 Collection date: {today}")
print(f"🔧 Tracking {len(issue_types)} issue types")
print(f"💾 Output will be saved to: {output_file}\n")

for country in countries:
    # Get proper display name (defaults to title case if not in our mapping)
    display_name = country_display_names.get(country, ' '.join([word.capitalize() for word in country.split('_')]))

    for issue_id, issue_name in issue_types.items():
        url = f"https://osmose.openstreetmap.fr/en/issues/open.csv?country={country}&item={issue_id}&limit=0"
        print(f"➡️  Processing {display_name} ({country}) - {issue_name}...", end=" ")

        for attempt in range(max_retries):
            try:
                response = requests.get(url, timeout=3600)
                response.raise_for_status()

                df = pd.read_csv(StringIO(response.text))
                if not df.empty:
                    df["country"] = display_name  # Use proper display name
                    df["region"] = country  # Keep original region code
                    df["date_collected"] = today
                    df["issue_type"] = issue_name

                    if all_data.empty:
                        all_data = df
                    else:
                        all_data = pd.concat([all_data, df], ignore_index=True)

                    print(f"✅ {len(df)} records")
                else:
                    print(f"⚠️  No records")
                break  # Success - exit retry loop

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 502 and attempt < max_retries - 1:
                    print(f"🔄 [Attempt {attempt + 1}]", end=" ")
                    time.sleep(retry_delay)
                    continue
                print(f"❌ HTTP Error {e.response.status_code}")
                break

            except requests.exceptions.RequestException as e:
                print(f"❌ Network error: {str(e)[:50]}...")
                break
            except Exception as e:
                print(f"❌ Unexpected error: {str(e)[:50]}...")
                break

        time.sleep(1)  # Be kind to the server

# Handle output file
if os.path.exists(output_file):
    print("\n📂 Existing file found, merging data...")
    old_data = pd.read_csv(output_file)

    if not all_data.empty:
        if old_data.empty:
            combined_data = all_data
        else:
            combined_data = pd.concat([old_data, all_data], ignore_index=True)

        # Remove potential duplicates
        dup_cols = [col for col in combined_data.columns if col not in ["date_collected", "region"]]
        combined_data = combined_data.drop_duplicates(subset=dup_cols, keep="last")

        combined_data.to_csv(output_file, index=False)
        new_records = len(all_data)
        total_records = len(combined_data)
        print(f"✨ Added {new_records} new records")
        print(f"📊 Total records now: {total_records}")
    else:
        print("⚠️  No new data to merge with existing file")
else:
    if not all_data.empty:
        print("\n🆕 Creating new data file...")
        all_data.to_csv(output_file, index=False)
        print(f"📊 File created with {len(all_data)} records")
    else:
        print("\n⚠️  No data collected - output file not created")

print("\n🏁 Data collection complete!")