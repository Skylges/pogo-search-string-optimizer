#!/usr/bin/env python3
"""
Rebuild data/processed/pok.csv, the lookup table mapping every
(Pokémon, form, shadow) combination to its PvPoke display name and
Pokémon GO search string.

Run this after a Pokémon GO content update adds new species/forms.
For normal day-to-day use (just generating search strings for the
current rankings), you don't need this script — pok.csv is already
committed and generate_search_strings.py reads it directly.

Usage:
    # Rebuild pok.csv using the existing data/raw/pokemon_forms_*.csv
    # and reusing cached evolution-line data wherever possible.
    python scripts/update_lookup_table.py

    # Also fetch a fresh forms list from pogoapi first.
    python scripts/update_lookup_table.py --fetch-forms

    # Force re-fetching every evolution line from PokeAPI (slow).
    python scripts/update_lookup_table.py --fetch-evolutions
"""

import argparse
import ast
import logging
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data_files import find_latest_file
from src.fetch_evolutions import build_evolution_cache
from src.fetch_pogoapi import fetch_pokemon_forms, save_pokemon_forms
from src.lookup_table import build_lookup_table, describe_unmatched, find_unmatched
from src.rankings import load_rankings

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Anchored to the project root, not the current working directory, so the
# script behaves the same whether you run it as `python
# scripts/update_lookup_table.py` from the repo root or launch it some
# other way (double-click, IDE "run" button, etc.).
PROJECT_ROOT = Path(__file__).resolve().parents[1]

FORMS_FILE_PATTERN = "pokemon_forms_*.csv"
DEFAULT_DATA_DIR = PROJECT_ROOT / "data" / "raw"
DEFAULT_LOOKUP_TABLE_PATH = PROJECT_ROOT / "data" / "processed" / "pok.csv"


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fetch-forms", action="store_true", help="Fetch a fresh forms list from pogoapi.net"
    )
    parser.add_argument(
        "--fetch-evolutions",
        action="store_true",
        help="Re-fetch every evolution line from PokeAPI instead of reusing the cache",
    )
    parser.add_argument(
        "--forms-file",
        default=None,
        help="Path to a specific pokemon_forms CSV. Defaults to the newest one in --data-dir.",
    )
    parser.add_argument("--lookup-table", default=str(DEFAULT_LOOKUP_TABLE_PATH))
    parser.add_argument(
        "--data-dir", default=str(DEFAULT_DATA_DIR), help="Directory with rankings/forms CSVs"
    )
    return parser.parse_args()


def load_evo_cache(existing_lookup_path, dex_numbers, force_refetch):
    """
    Build a {dex: [evo_ids...]} cache, reusing the previous pok.csv where
    possible and only hitting PokeAPI for dex numbers that are new or
    when a full refetch is requested.
    """
    cache = {}

    if not force_refetch and Path(existing_lookup_path).exists():
        old = pd.read_csv(existing_lookup_path)
        old["evo_ids"] = old["evo_ids"].apply(ast.literal_eval)
        cache = dict(zip(old["dex"], old["evo_ids"]))

    missing = sorted(set(dex_numbers) - cache.keys())

    if force_refetch:
        missing = sorted(set(dex_numbers))

    if missing:
        logger.info("Fetching evolution lines for %d dex numbers", len(missing))
        cache.update(build_evolution_cache(missing))

    return cache


def main():
    args = parse_args()

    if args.fetch_forms:
        forms_df = fetch_pokemon_forms()
        save_pokemon_forms(forms_df, args.data_dir)
    else:
        forms_path = args.forms_file or find_latest_file(FORMS_FILE_PATTERN, args.data_dir)
        logger.info("Loading forms from %s", forms_path)
        forms_df = pd.read_csv(forms_path)

    evo_cache = load_evo_cache(
        args.lookup_table, forms_df["pokemon_id"].unique(), args.fetch_evolutions
    )

    pok_df = build_lookup_table(forms_df, evo_cache)

    # Validate against the current rankings before saving.
    leagues = load_rankings(args.data_dir)
    for league_name, league_df in leagues.items():
        unmatched = find_unmatched(league_df, pok_df)
        if unmatched.empty:
            continue

        logger.warning("Unmatched Pokémon in %s: %d", league_name, len(unmatched))
        print(describe_unmatched(unmatched, pok_df).to_string(index=False))

    Path(args.lookup_table).parent.mkdir(parents=True, exist_ok=True)
    pok_df.to_csv(args.lookup_table, index=False)
    logger.info("Saved %d rows to %s", len(pok_df), args.lookup_table)


if __name__ == "__main__":
    main()
