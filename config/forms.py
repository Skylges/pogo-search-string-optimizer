"""
Static configuration for Pokémon form handling.

This is all data, not logic — it's kept separate from src/ so that
updating for a new Pokémon GO release (new forms, new exceptions)
never requires touching the transformation code.
"""

# PVP-relevant forms as reported by pogoapi. Pokémon with multiple forms
# that share identical PvP stats only need to be listed once here.
PVP_FORMS = [
    "Normal", "Alola", "Galarian", "Hisuian", "Paldea", "Origin", "Altered",
    "Incarnate", "Therian", "Attack", "Defense", "Speed", "Dusk", "Midday",
    "Midnight", "Black", "White", "Plant", "Sandy", "Trash", "East_sea",
    "West_sea", "Fan", "Frost", "Heat", "Mow", "Wash", "Rainy", "Snowy",
    "Sunny", "Overcast", "Standard", "Zen", "Dawn_wings", "Dusk_mane",
    "Rapid_strike", "Single_strike", "Ice_rider", "Shadow_rider",
    "Disguised", "Shield", "Large", "Small", "Super", "Average",
    "Full_belly", "Female", "Male", "Family_of_four", "Amped", "Three",
    "00", "Dandy", "Complete", "Fifty_percent", "Ten_percent",
    "Paldea_aqua", "Paldea_blaze", "Paldea_combat", "Autumn",
    "Blue_striped", "Sunshine", "Phony", "Land", "Sky", "Baile", "Pau",
    "Pompom", "Sensu", "Galarian_standard", "Archipelago", "Curly",
    "Droopy", "Stretchy",
    "A",  # Pogoapi uses this for both Unown (A) and Mewtwo (A).
    "Crowned_sword", "Hero", "Crowned_shield", "Resolute", "Ordinary",
    "Aria", "Shock", "Chill", "Burn", "Douse", "Masterpiece",
    "Unremarkable", "Confined", "Unbound"
]

# Conversion from the form name pogoapi uses to the form name PvPoke uses.
FORM_SUFFIX = {
    "Alola": "Alolan",
    "Paldea": "Paldean",
    "Complete": "Complete Forme",
    "Fifty_percent": "50% Forme",
    "Ten_percent": "10% Forme",
    "Paldea_aqua": "Aqua",
    "Paldea_blaze": "Blaze",
    "Paldea_combat": "Combat",
    "Pompom": "Pom-Pom",
    "Pau": "Pa'u",
    "Galarian_standard": "Galarian",
    "A": "Armored",  # Mewtwo (A). Unown (A) is fixed via PVPOKE_FORM_EXCEPTIONS.
    "Crowned_sword": "Crowned Sword",
    "Crowned_shield": "Crowned Shield",
    "Dawn_wings": "Dawn Wings",
    "Dusk_mane": "Dusk Mane",
}

# Forms that are filterable in the Pokémon GO search bar.
# Maps pogoapi form name -> the keyword used in the in-game search string.
REGIONAL_FORMS = {
    "Alola": "alola",
    "Galarian": "galar",  # Pogoapi: "Galarian" / Pokémon GO search: "galar"
    "Hisuian": "hisui",
    "Paldea": "paldea",
}

# Pokémon whose pogoapi form should NOT get a form suffix in PvPoke naming,
# because the form has identical PvP stats to the base form.
PVPOKE_FORM_EXCEPTIONS = {
    "Florges", "Floette", "Squawkabilly", "Mimikyu", "Frillish", "Jellicent",
    "Pyroar", "Runerigus", "Maushold", "Gastrodon", "Toxtricity",
    "Dudunsparce", "Spinda", "Furfrou", "Perrserker", "Sirfetch'd",
    "Obstagoon", "Sawsbuck", "Basculin", "Polteageist", "Shellos",
    "Deerling", "Mr. Rime", "Vivillon", "Flabebe", "Unown", "Sinistcha",
    "Scatterbug",
}

# One-off name overrides where PvPoke's naming diverges from pogoapi's.
PVPOKE_NAME_EXCEPTIONS = {
    "Nidoran♀": "Nidoran Female",
    "Nidoran♂": "Nidoran Male",
    "Mime Jr.": "Mime (Jr)",
}

# Evolution-line overrides for cases where the naive "evolves_from" walk
# up PokeAPI gives the wrong answer for a specific form.
EVO_EXCEPTIONS = {
    (26, "Alola"): [25, 26],     # Raichu (Alolan) can't be from Pichu
    (122, "Galarian"): [122],    # Galarian Mr. Mime can't be from Mime Jr.
    (866, "Galarian"): [122, 866],  # Galarian Mr. Rime can't be from Mime Jr.
}
