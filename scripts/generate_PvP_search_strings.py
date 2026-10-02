#!/usr/bin/env python3
"""
Print an optimized Pokémon GO search string for the top N Pokémon in
each league's current PvPoke rankings.

Usage:
    python scripts/generate_PvP_search_strings.py
    python scripts/generate_PvP_search_strings.py --top 20 --data-dir data/raw
    python scripts/generate_PvP_search_strings.py --league GL
"""

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.PvP import LEAGUE_FILE_PATTERNS, load_pvp_rankings, print_pvp_rankings
from src.search_strings import lookup_search_strings, optimize_pokemon_search


logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Anchored to the project root, not the current working directory, so the
# script behaves the same regardless of where it's launched from.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PVPOKE_DIR = PROJECT_ROOT / "data" / "raw" / "PvPoke"
DEFAULT_FORMS_DIR = PROJECT_ROOT / "data" / "raw" / "PogoAPI"
DEFAULT_LOOKUP_TABLE_PATH = PROJECT_ROOT / "data" / "processed" / "pok.csv"


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--top", type=int, default=30, help="Number of top Pokémon to consider per league"
    )
    parser.add_argument(
        "--league",
        choices=sorted(LEAGUE_FILE_PATTERNS),
        default=None,
        help="Only generate a search string for this league (default: all leagues)",
    )
    parser.add_argument(
        "--data-dir", default=str(DEFAULT_PVPOKE_DIR), help="Directory containing the PvP rankings CSVs"
    )
    parser.add_argument(
        "--lookup-table",
        default=str(DEFAULT_LOOKUP_TABLE_PATH),
        help="Path to the pok.csv lookup table",
    )
    parser.add_argument(
        "--print-rankings", default=True, help="Print the top N Pokémon in each league's rankings (default: False)"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    pok_df = pd.read_csv(args.lookup_table)

    patterns = LEAGUE_FILE_PATTERNS
    if args.league:
        patterns = {args.league: LEAGUE_FILE_PATTERNS[args.league]}

    leagues = load_pvp_rankings(args.data_dir, patterns=patterns)
    
    all_names = []

    for league_name, league_df in leagues.items():
        names = league_df.head(args.top)["Pokemon"].tolist()
        all_names.extend(names)
        
        strings = lookup_search_strings(names, pok_df, mode="PVP")
        optimized = optimize_pokemon_search(strings)

        print("=" * 40)
        print(f" {league_name} - Top {args.top} Pokémon")
        print("=" * 40)
        print(optimized)

    # All PvP Pokemon combined
    all_names = list(dict.fromkeys(all_names))
    search_strings = lookup_search_strings(all_names, pok_df, mode="PVP")
    optimized = optimize_pokemon_search(search_strings)

    print("=" * 40)
    print(f" All PvP mons - {len(all_names)} Pokémon")
    print("=" * 40)
    print(optimized)
    print()
        
    if args.print_rankings:
        for league_name, league_df in leagues.items():
            print_pvp_rankings(league_name, league_df, top_n=args.top)

if __name__ == "__main__":
    main()