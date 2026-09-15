"""
Fetch full evolution lines from PokeAPI for a set of Pokédex numbers.

Also only needs to run after a content update adds new species — the
result should be cached (pok.csv's evo_ids column) and reused otherwise,
since this makes one or more HTTP requests per unique dex number.
"""

import logging

import requests

logger = logging.getLogger(__name__)

POKEAPI_SPECIES_URL = "https://pokeapi.co/api/v2/pokemon-species/{dex}"


def get_evolution_line(dex):
    """Walk PokeAPI's evolves_from chain back to the base form for `dex`."""
    evo_line = [dex]

    species = requests.get(POKEAPI_SPECIES_URL.format(dex=dex)).json()

    while species["evolves_from_species"]:
        species = requests.get(species["evolves_from_species"]["url"]).json()
        evo_line.append(species["id"])

    return sorted(evo_line)


def build_evolution_cache(dex_numbers):
    """Return {dex: [evo_ids...]} for every dex number in dex_numbers."""
    cache = {}

    for dex in dex_numbers:
        logger.info("Fetching evolution line for dex %s", dex)
        cache[dex] = get_evolution_line(dex)

    return cache
