#!/usr/bin/env python3
"""
Fetch DialgaDex raid attacker rankings for each type and cache them as
CSVs under data/raw/Dialgadex/.

Requires Playwright's browser binaries installed once:
    playwright install chromium

Usage:
    python scripts/update_raid_attackers.py
    python scripts/update_raid_attackers.py --type Water --top 20
    python scripts/update_raid_attackers.py --dump-html Water
"""

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.raid_attackers import (
    RAID_TYPES,
    dump_rendered_html,
    fetch_type_rankings,
    save_raid_rankings
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = PROJECT_ROOT / "data" / "raw" / "Dialgadex"


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--type", choices=RAID_TYPES, default=None, help="Only fetch this attacker type"
    )
    parser.add_argument(
        "--top", type=int, default=75, help="Only keep the top N per type (default: 100)"
    )
    parser.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR))
    parser.add_argument(
        "--dump-html",
        metavar="TYPE",
        help="Don't fetch — just render one type's page and save the HTML for inspection "
        "(useful if DialgaDex's markup ever changes and parsing breaks)",
    )
    parser.add_argument("--out", default= DEFAULT_DATA_DIR / "rendered_dialgadex.html", help="Path for --dump-html")
    return parser.parse_args()


def main():
    args = parse_args()

    rankings = []
    
    if args.dump_html:
        dump_rendered_html(args.dump_html, args.out)
        return

    types = [args.type] if args.type else RAID_TYPES
    rankings = []

    for attacker_type in types:
        type_rankings = fetch_type_rankings(
            attacker_type,
            top_n=args.top,
        )

        if not type_rankings:
            logger.warning(
                "No Pokémon found for %s — DialgaDex's markup may have changed. "
                "Try --dump-html %s and check NAME_SELECTOR in src/raid_attackers.py.",
                attacker_type,
                attacker_type,
            )
            continue

        rankings.extend(type_rankings)

    save_raid_rankings(rankings, args.data_dir)

if __name__ == "__main__":
    main()