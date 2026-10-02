from src.data_files import find_latest_file
from src.raid_attackers import load_raid_rankings


rankings_df = load_raid_rankings()

# Print all unique forms
print("Unique forms in the raid rankings:")
unique_forms = rankings_df["Form"].dropna().unique()
for form in unique_forms:
    print(f" - {form}")