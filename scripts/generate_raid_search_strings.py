#!/usr/bin/env python3
"""
Print an optimized Pokémon GO search string for the top N raid
attackers per type, from the raid rankings cached by
update_raid_attackers.py. Reads only local files — no network calls.

Usage:
    python scripts/generate_raid_search_strings.py
    python scripts/generate_raid_search_strings.py --type Fire --top 10
"""

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.raid_attackers import load_raid_rankings, print_raid_rankings
from src.search_strings import optimize_pokemon_search
from src.search_strings import lookup_search_strings

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = PROJECT_ROOT / "data" / "raw" / "Dialgadex"
DEFAULT_LOOKUP_TABLE_PATH = PROJECT_ROOT / "data" / "processed" / "pok.csv"


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--top", type=int, default=5, help="Number of top attackers to consider per type"
    )
    parser.add_argument(
        "--type", default=None, help="Only generate a string for this attacker type (e.g. Fire)"
    )
    parser.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR))
    parser.add_argument("--lookup-table", default=str(DEFAULT_LOOKUP_TABLE_PATH))
    parser.add_argument("--print-rankings", default=True, help="Print the top N attackers for each type (default: True)")
    return parser.parse_args()


def main():
    args = parse_args()

    pok_df = pd.read_csv(args.lookup_table)
    rankings_df = load_raid_rankings(args.data_dir)

    types = [args.type] if args.type else sorted(rankings_df["Type"].unique())
    all_names = []
    
    for attacker_type in types:
        type_df = (
            rankings_df[rankings_df["Type"] == attacker_type]
            .sort_values("Rank")
            .head(args.top)
        )

        if type_df.empty:
            logger.warning("No cached rankings found for type %s", attacker_type)
            continue

        names = type_df["Pokemon"].tolist()
        all_names.extend(names)
        search_strings = lookup_search_strings(names, pok_df, mode="Raid")
        optimized = optimize_pokemon_search(search_strings)

        print("=" * 40)
        print(f" {attacker_type} - Top {len(type_df)} Attackers")
        print("=" * 40)
        print(optimized)
        print()  
        
        if args.print_rankings:
            print_raid_rankings(type_df, top_n=args.top)
            
    # All raid attackers combined
    all_names = list(dict.fromkeys(all_names))
    search_strings = lookup_search_strings(all_names, pok_df, mode="Raid")
    optimized = optimize_pokemon_search(search_strings)

    print("=" * 40)
    print(f" All Raid Attackers - {len(all_names)} Pokémon")
    print("=" * 40)
    print(optimized)
    print()
        


if __name__ == "__main__":
    main()