"""
Resolve a league's ranked Pokémon list into individual PvPoke search
strings, ready to be combined by search_optimizer.optimize_pokemon_search.
"""

import logging

logger = logging.getLogger(__name__)


def make_search_strings(league_df, pok_df):
    """
    For each row in a league's rankings, look up its pre-computed
    search_string from pok_df (matched by pvpoke_name, case-insensitive).
    """
    search_strings = []

    for _, row in league_df.iterrows():
        dex = row["Dex"]
        pvpoke_name = row["Pokemon"]

        matches = pok_df.loc[
            pok_df["pvpoke_name"].str.lower() == pvpoke_name.lower(), "search_string"
        ]

        if matches.empty:
            logger.warning("No match found for %s (Dex: %s)", pvpoke_name, dex)
            continue

        search_string = matches.iloc[0]

        if not search_string:
            logger.warning("No search string for %s (Dex: %s)", pvpoke_name, dex)
            continue

        search_strings.append(search_string)

    return search_strings
