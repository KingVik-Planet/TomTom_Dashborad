import pandas as pd
import requests
import os
from datetime import date
from io import StringIO

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

all_data = pd.DataFrame()
today = date.today().isoformat()

for country in countries:
    url = f"https://osmose.openstreetmap.fr/en/issues/open.csv?country={country}&limit=0"
    print(f"Processing {country} ...")
    try:
        response = requests.get(url, timeout=3600)
        response.raise_for_status()
        df = pd.read_csv(StringIO(response.text))
        df["country"] = country
        df["date_collected"] = today
        all_data = pd.concat([all_data, df], ignore_index=True)
        print(f"{country}: {len(df)} records downloaded")
    except Exception as e:
        print(f"Failed for {country}: {e}")

# File path
output_file = r"C:\Users\chukw\OneDrive\Documentos\TomTom Event\osmose_africa.csv"

# If file exists, append to it
if os.path.exists(output_file):
    print("Existing file found, appending data...")
    old_data = pd.read_csv(output_file)
    combined_data = pd.concat([old_data, all_data], ignore_index=True)
    combined_data.to_csv(output_file, index=False)
    print(f"\nAppended today's data. Total rows now: {len(combined_data)}")
else:
    print("No existing file, creating new one...")
    all_data.to_csv(output_file, index=False)
    print(f"\nFile created with {len(all_data)} records")
