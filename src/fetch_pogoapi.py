"""
One-time fetches against pogoapi.net.

These calls only need to be re-run after a Pokémon GO content update
adds new species/forms. Normal runs should use the cached CSVs these
functions produce instead of hitting the network every time — see
scripts/update_lookup_table.py.
"""

import logging
from datetime import date
from pathlib import Path

import pandas as pd
import requests

logger = logging.getLogger(__name__)

POKEMON_TYPES_URL = "https://pogoapi.net/api/v1/pokemon_types.json"


def fetch_pokemon_forms():
    """
    Fetch every Pokémon form from pogoapi.

    Uses the "types" endpoint rather than the dedicated forms endpoint,
    because the forms endpoint only returns a list of unique form names,
    not which Pokémon have them.
    """
    logger.info("Fetching Pokémon forms from %s", POKEMON_TYPES_URL)
    data = requests.get(POKEMON_TYPES_URL).json()

    forms_df = pd.DataFrame(data, columns=["pokemon_id", "pokemon_name", "form"])

    # Two exceptions that were easier to fix here than downstream.
    # Meowstic: pogoapi uses "Normal" for the default form, PvPoke uses "Male"/"Female".
    forms_df.loc[
        (forms_df["pokemon_id"] == 678) & (forms_df["form"] == "Normal"), "form"
    ] = "Male"

    # Cherrim: pogoapi uses "Sunny" for the default form, PvPoke uses "Sunshine".
    forms_df.loc[
        (forms_df["pokemon_id"] == 421) & (forms_df["form"] == "Sunny"), "form"
    ] = "Sunshine"

    return forms_df


def dated_forms_filename(data_dir, on_date=None):
    """
    Build a dated forms filename, e.g. data/raw/pokemon_forms_09_2026.csv,
    matching this project's convention of stamping the download month
    onto fetched assets.
    """
    on_date = on_date or date.today()
    return str(Path(data_dir) / f"pokemon_forms_{on_date:%m_%Y}.csv")


def save_pokemon_forms(forms_df, data_dir="data/raw", on_date=None):
    """Save forms_df under a dated filename inside data_dir and return the path."""
    Path(data_dir).mkdir(parents=True, exist_ok=True)
    path = dated_forms_filename(data_dir, on_date)

    forms_df.to_csv(path, index=False)
    logger.info("Saved %d forms to %s", len(forms_df), path)
    return path
