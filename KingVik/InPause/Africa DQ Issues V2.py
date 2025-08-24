import pandas as pd
import requests
import os
from datetime import date
from io import StringIO

# Configuration
output_dir = r"C:\Users\chukw\OneDrive\Documentos\TomTom Event"
os.makedirs(output_dir, exist_ok=True)
output_file = os.path.join(output_dir, "osmose_africa.csv")

# African countries list
countries = [
    "algeria", "angola", "benin", "botswana", "burkina faso", "burundi",
    "cabo verde", "cameroon", "central african republic", "chad", "comoros",
    "congo brazzaville", "congo kinshasa", "djibouti", "egypt", "equatorial guinea",
    "eritrea", "eswatini", "ethiopia", "gabon", "gambia", "ghana", "guinea",
    "guinea-bissau", "ivory coast", "kenya", "lesotho", "liberia", "libya",
    "madagascar", "malawi", "mali", "mauritania", "mauritius", "morocco",
    "mozambique", "namibia", "niger", "nigeria", "rwanda", "sao tome and principe",
    "senegal", "seychelles", "sierra leone", "somalia", "south africa", "south sudan",
    "sudan", "tanzania", "togo", "tunisia", "uganda", "zambia", "zimbabwe"
]

today = date.today().isoformat()
all_data = pd.DataFrame()

print(f"\n🌍 Starting OSMOSE data collection for {len(countries)} African countries")
print(f"📅 Collection date: {today}\n")

for country in countries:
    url = f"https://osmose.openstreetmap.fr/en/issues/open.csv?country={country}&limit=0"
    print(f"➡️  Processing {country.title()}...", end=" ")

    try:
        response = requests.get(url, timeout=3600)
        response.raise_for_status()

        df = pd.read_csv(StringIO(response.text))
        if not df.empty:  # Only process if DataFrame is not empty
            df["country"] = country
            df["date_collected"] = today

            if all_data.empty:
                all_data = df
            else:
                all_data = pd.concat([all_data, df], ignore_index=True)

            print(f"✅ {len(df)} records downloaded")
        else:
            print(f"⚠️  No records found")

    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {str(e)[:50]}...")
    except Exception as e:
        print(f"❌ Processing error: {str(e)[:50]}...")

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
        dup_cols = [col for col in combined_data.columns if col != "date_collected"]
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