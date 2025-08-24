import pandas as pd

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

#countries = ["nigeria", "ghana", "togo", "benin", "kenya", "rwanda", "south africa", "uganda", "zambia", "ethiopia"]
all_data = pd.DataFrame()

for country in countries:
    url = f"https://osmose.openstreetmap.fr/en/issues/open.csv?country={country}&limit=0"
    try:
        df = pd.read_csv(url)
        df["country"] = country
        all_data = pd.concat([all_data, df], ignore_index=True)
        print(f"{country}: {len(df)} records downloaded")
    except Exception as e:
        print(f"Failed for {country}: {e}")

all_data.to_csv("osmose_africa.csv", index=False)
print(f"\nTotal records: {len(all_data)}")
