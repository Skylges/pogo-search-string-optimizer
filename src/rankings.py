"""
Load PvPoke "overall rankings" CSV exports for each league.

Filenames from PvPoke include a download date (e.g.
cp1500_all_overall_rankings_10_09_26.csv), which changes every time you
re-download them. Rather than hardcoding a date, this module picks the
most recently modified file matching each league's pattern.
"""

import logging

import pandas as pd

from src.data_files import find_latest_file

logger = logging.getLogger(__name__)

# Maps a short league code to the filename glob pattern PvPoke exports use.
LEAGUE_FILE_PATTERNS = {
    "LL": "cp500_little_overall_rankings_*.csv",
    "GL": "cp1500_all_overall_rankings_*.csv",
    "UL": "cp2500_all_overall_rankings_*.csv",
    "ML": "cp10000_all_overall_rankings_*.csv",
}


def load_rankings(data_dir=".", patterns=None):
    """
    Load one DataFrame per league from data_dir.

    Returns a dict: {"LL": df, "GL": df, "UL": df, "ML": df}
    """
    patterns = patterns or LEAGUE_FILE_PATTERNS
    leagues = {}

    for league_name, pattern in patterns.items():
        path = find_latest_file(pattern, data_dir)
        logger.info("Loading %s rankings from %s", league_name, path)
        leagues[league_name] = pd.read_csv(path, header=0)

    return leagues
