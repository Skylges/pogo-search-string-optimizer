# PvP Search Strings

Generates an optimized Pokémon GO in-game search string for the top-ranked
Pokémon in each PvP league (Little, Great, Ultra, Master), based on
[PvPoke](https://pvpoke.com/) rankings. Instead of checking PvPoke for good species and going through your storage one by one,
just paste the generated string into the game's search bar and it filters straight to them.
This project created a database of search strings which include forms (galar, alolan, etc.) and shadow forms.
By using a CNF-based search string optimizer, these can be searched for and combined in relatively short single string.

## How it works

1. **`data/processed/pok.csv`** is a lookup table mapping every
   `(Pokémon, form, shadow)` combination to its PvPoke display name and
   the raw Pokémon GO search string that matches it (e.g.
   `957,958,959&!shadow`).
2. **`scripts/generate_search_strings.py`** reads the current PvPoke
   rankings CSVs, looks up each top Pokémon's search string in `pok.csv`,
   and combines them all into one optimized string using a small CNF
   (conjunctive normal form) simplifier — see `src/search_optimizer.py`.
3. **`scripts/update_lookup_table.py`** rebuilds `pok.csv` from scratch.
   You only need this after a Pokémon GO content update adds new species
   or forms.

## Notes & caveats

- **Every entry has a Shadow row, whether or not it's real.** `pok.csv`
  contains a `shadow=True` row for every single `(Pokémon, form)`
  combination, not just the ones that actually exist as Shadow in the
  game. pogoapi's "which Pokémon can be Shadow" data is outdated, so
  rather than risk missing real Shadow mons, every row gets a Shadow
  variant generated. A `shadow=True` row means "here's the search
  string *if* this exists as a Shadow", not a guarantee it does.
- **`evo_ids` is per-form, not per-species.** It lists only the dex
  numbers that can actually evolve into *that specific row's* PvPoke
  form — not every Pokémon the base species could ever become. This is
  what lets the search string also catch an un-evolved copy sitting in
  storage (e.g. Vulpix shows up when searching for Ninetales). Regional
  forms narrow this further: Alolan Raichu's `evo_ids` is `[25, 26]`
  (Pikachu, Raichu), not the full `[172, 25, 26]` chain, because a
  regular Pichu can't evolve into the Alolan form. See
  `EVO_EXCEPTIONS` in `config/forms.py` for these overrides.

## Setup

```bash
pip install -r requirements.txt
```

Download the "overall rankings" CSV for each league from PvPoke's
rankings pages and put them in `data/raw/` (any filename matching
`cp500_little_overall_rankings_*.csv`, `cp1500_all_overall_rankings_*.csv`,
`cp2500_all_overall_rankings_*.csv`, `cp10000_all_overall_rankings_*.csv`
works — the most recently downloaded one is picked automatically).

## Usage

Generate search strings for the top 30 Pokémon in each league:

```bash
python scripts/generate_search_strings.py
```

Adjust how many Pokémon per league:

```bash
python scripts/generate_search_strings.py --top 20
```

Only generate a string for one league:

```bash
python scripts/generate_search_strings.py --league GL
```

## Updating after a game update

```bash
# Fetch a fresh forms list and rebuild pok.csv, only hitting PokeAPI
# for evolution lines of newly-added Pokémon.
python scripts/update_lookup_table.py --fetch-forms

# Force a full re-fetch of every evolution line (slow, rarely needed).
python scripts/update_lookup_table.py --fetch-forms --fetch-evolutions
```

The script prints any Pokémon in the current rankings that it couldn't
match to a `pok.csv` entry, which usually means a new form needs a
naming exception added to `config/forms.py`.

## Project layout

```
config/forms.py                 # Static form/name/evolution exception data
src/search_optimizer.py         # Pure CNF search-string combiner (tested)
src/lookup_table.py             # Builds pok_df: naming + search strings
src/league_search_strings.py    # Resolves a league's ranked list -> search strings
src/rankings.py                 # Loads PvPoke rankings CSVs
src/data_files.py               # Shared "find latest dated file" helper
src/fetch_pogoapi.py            # One-time pogoapi.net form fetch
src/fetch_evolutions.py         # One-time PokeAPI evolution-line fetch
scripts/generate_search_strings.py   # Main entry point
scripts/update_lookup_table.py       # Maintenance entry point
tests/test_search_optimizer.py       # Unit tests for the optimizer
data/raw/                       # Downloaded rankings + forms CSVs (gitignored by default)
data/processed/pok.csv          # The lookup table
```

## Workflow

```mermaid
flowchart TD
    subgraph M["Maintenance — update_lookup_table.py \n(occasional, after a game update adds new Pokémon)"]
        A1["fetch_pokemon_forms()\npogoapi.net"] --> A2["save_pokemon_forms()\ndata/raw/pokemon_forms_MM_YYYY.csv"]
        A2 --> A3["build_lookup_table()"]
        A3 --> A3a["filter_pvp_forms()\nbuild_base_table()\nbuild_pvpoke_names()"]
        A3a --> A3b["apply_evo_ids()\nbuild_evolution_cache()"]
        A3b --> A3c["build_search_strings()"]
        A3c --> A4["find_unmatched() / describe_unmatched()\nvalidate against rankings"]
        A4 --> A5["pok_df.to_csv()\nSave data/processed/pok.csv"]
    end

    subgraph D["You — manual download (before each run with fresh data)"]
        D1["Download 'overall rankings' CSV\nfrom pvpoke.com for each league"] --> D2["Save into data/raw/\nmatching cp*_overall_rankings_*.csv"]
    end

    subgraph R["Regular use — generate_search_strings.py (every run, no network)"]
        B1["pd.read_csv()\nLoad pok.csv"] --> B4
        B2["load_rankings()"] --> B2a["find_latest_file()\npicks newest CSV per league"]
        B2a --> B4
        B4["make_search_strings()\nmatch Pokemon → search_string\n(region/shadow aware)"] --> B5
        B5["optimize_pokemon_search()\nparse_search_term() · is_tautology()\nremove_redundant_clauses()"] --> B6["Print optimized search string"]
    end

    A5 -.-> B1
    D2 -.-> B2
```

## Example output (PvPoke rankings September 2026)

```
========================================
 LL - Top 30 Pokémon
========================================
!shadow,104,147,165,194,207,339,37,425,434,509,622&!shadow,104,147,165,194,207,339,425,434,509,622,alola&!paldea,!shadow,104,147,165,207,339,37,425,434,509,622&!paldea,!shadow,104,147,165,207,339,425,434,509,622,alola&104,108,133,194,207,263,320,360,37,436,447,580,616,624,629,633,86,971,shadow&104,108,133,194,207,320,360,37,436,447,580,616,624,629,633,86,971,galar,shadow&104,108,133,194,207,263,320,360,436,447,580,616,624,629,633,86,971,alola,shadow&104,108,133,194,207,320,360,436,447,580,616,624,629,633,86,971,alola,galar,shadow&104,108,133,147,165,194,207,263,320,339,360,37,425,434,436,447,509,580,616,622,624,629,633,86,971&104,108,133,147,165,194,207,320,339,360,37,425,434,436,447,509,580,616,622,624,629,633,86,971,galar&104,108,133,147,165,194,207,263,320,339,360,425,434,436,447,509,580,616,622,624,629,633,86,971,alola&104,108,133,147,165,194,207,320,339,360,425,434,436,447,509,580,616,622,624,629,633,86,971,alola,galar

========================================
 GL - Top 30 Pokémon
========================================
!shadow,194,195,333,334,37,38,393,394,395,821,822,823&!alola,!shadow,194,195,333,334,393,394,395,821,822,823&!alola,143,158,159,160,161,162,183,184,194,195,21,22,222,226,287,288,298,333,334,386,393,394,395,446,458,56,57,592,593,669,670,671,751,752,778,808,809,821,822,823,827,828,845,957,958,959,979,980&!alola,143,158,159,160,161,162,183,184,194,195,21,22,226,287,288,298,333,334,386,393,394,395,446,458,56,57,592,593,669,670,671,751,752,778,808,809,821,822,823,827,828,845,957,958,959,979,980,galar&104,105,143,158,159,160,161,162,183,184,194,195,21,22,222,226,287,288,298,333,334,37,38,386,393,394,395,446,458,56,57,592,593,669,670,671,751,752,778,808,809,821,822,823,827,828,845,957,958,959,979,980&104,105,143,158,159,160,161,162,183,184,194,195,21,22,226,287,288,298,333,334,37,38,386,393,394,395,446,458,56,57,592,593,669,670,671,751,752,778,808,809,821,822,823,827,828,845,957,958,959,979,980,galar

========================================
 UL - Top 30 Pokémon
========================================
!shadow,131,143,158,159,160,355,356,37,38,393,394,395,446,477,821,822,823&!shadow,131,143,158,159,160,355,356,393,394,395,446,477,821,822,823,alola&131,143,146,158,159,160,355,356,37,379,38,393,394,395,446,477,487,592,593,640,669,670,671,7,718,778,799,8,808,809,810,811,812,821,822,823,845,9,909,910,911,957,958,959,977&131,143,146,158,159,160,355,356,379,393,394,395,446,477,487,592,593,640,669,670,671,7,718,778,799,8,808,809,810,811,812,821,822,823,845,9,909,910,911,957,958,959,977,alola&131,143,158,159,160,355,356,37,379,38,393,394,395,446,477,487,592,593,640,669,670,671,7,718,778,799,8,808,809,810,811,812,821,822,823,845,9,909,910,911,957,958,959,977,galar&131,143,158,159,160,355,356,379,393,394,395,446,477,487,592,593,640,669,670,671,7,718,778,799,8,808,809,810,811,812,821,822,823,845,9,909,910,911,957,958,959,977,alola,galar

========================================
 ML - Top 30 Pokémon
========================================
!shadow,216,217,249,374,375,376,443,444,445,484,643,901&216,217,249,250,374,375,376,382,383,443,444,445,483,484,643,644,646,647,716,718,789,790,792,800,802,808,809,888,889,890,901
```