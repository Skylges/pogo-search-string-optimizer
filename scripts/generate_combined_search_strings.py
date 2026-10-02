import argparse

import pandas as pd
import sys
from pathlib import Path
import logging

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
PROJECT_ROOT = Path(__file__).resolve().parents[1]

from src.PvP import load_pvp_rankings, LEAGUE_FILE_PATTERNS
from src.raid_attackers import load_raid_rankings
from src.search_strings import optimize_pokemon_search, lookup_search_strings

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_PVPOKE_DIR = PROJECT_ROOT / "data" / "raw" / "PvPoke"
DEFAULT_DIALGADEX_DIR = PROJECT_ROOT / "data" / "raw" / "Dialgadex"

def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a combined Pokémon GO search string from PvP and raid rankings."
    )

    parser.add_argument(
        "--pvp_top",
        type=int,
        default=50,
        help="Number of top Pokémon per PvP league (default: 50)",
    )

    parser.add_argument(
        "--raid_top",
        type=int,
        default=5,
        help="Number of top attackers per raid type (default: 5)",
    )

    parser.add_argument(
        "--league",
        choices=LEAGUE_FILE_PATTERNS.keys(),
        help="Only include this PvP league",
    )

    parser.add_argument(
        "--lookup-table",
        default="data/processed/pok.csv",
        help="Path to the Pokémon lookup table",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    pok_df = pd.read_csv(args.lookup_table)

    # PvP
    patterns = LEAGUE_FILE_PATTERNS
    if args.league:
        patterns = {
            args.league: LEAGUE_FILE_PATTERNS[args.league]
        }

    leagues = load_pvp_rankings(
        DEFAULT_PVPOKE_DIR,
        patterns=patterns,
    )

    pvp_search_strings = []

    for league_name, league_df in leagues.items():
        names = league_df.head(args.pvp_top)["Pokemon"].tolist()

        pvp_search_strings.extend(
            lookup_search_strings(
                names,
                pok_df,
                mode="PVP",
            )
        )

    # Raids
    rankings_df = load_raid_rankings(DEFAULT_DIALGADEX_DIR)

    raid_search_strings = []

    types = sorted(rankings_df["Type"].unique())

    for attacker_type in types:
        type_df = (
            rankings_df[rankings_df["Type"] == attacker_type]
            .sort_values("Rank")
            .head(args.raid_top)
        )

        if type_df.empty:
            logger.warning("No cached rankings found for type %s", attacker_type)
            continue

        names = type_df["Pokemon"].tolist()

        raid_search_strings.extend(
            lookup_search_strings(
                names,
                pok_df,
                mode="Raid",
            )
        )

    # Combine and optimize
    search_strings = pvp_search_strings + raid_search_strings
    optimized = optimize_pokemon_search(search_strings)

    print("=" * 40)
    print(" Combined top", args.pvp_top, "PvP + top ", args.raid_top, "Raid attackers")
    print("=" * 40)
    print(optimized)
    print()


if __name__ == "__main__":
    main()