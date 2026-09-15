"""
Shared helper for finding the most recent dated data file matching a
glob pattern (e.g. "pokemon_forms_*.csv" -> pokemon_forms_09_2026.csv).

Downloaded/fetched assets in this project keep a date in the filename
(pokemon_forms_09_2026.csv, cp1500_all_overall_rankings_10_09_26.csv,
...) so you can tell at a glance how stale a file is. Code that reads
them should never hardcode that date — it should glob for the pattern
and pick the newest match instead.
"""

import glob
import os


def find_latest_file(pattern, data_dir):
    """Return the most recently modified file in data_dir matching pattern."""
    matches = glob.glob(os.path.join(data_dir, pattern))

    if not matches:
        resolved = os.path.abspath(data_dir)
        raise FileNotFoundError(
            f"No file matching '{pattern}' found in '{data_dir}' "
            f"(resolved to '{resolved}'). Check that this directory exists "
            f"and that you're running the script from the expected location."
        )

    return max(matches, key=os.path.getmtime)
