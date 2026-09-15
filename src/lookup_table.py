"""
Build the pok_df lookup table: one row per (Pokémon, form, shadow) with
its PvPoke display name and its optimized Pokémon GO search string.

This is the data pipeline behind pok.csv. Normal usage (generating
search strings for the current rankings) only needs the finished
pok.csv — this module is what scripts/update_lookup_table.py uses to
regenerate it after a game content update.
"""

import logging

import pandas as pd

from config.forms import (
    EVO_EXCEPTIONS,
    FORM_SUFFIX,
    PVP_FORMS,
    PVPOKE_FORM_EXCEPTIONS,
    PVPOKE_NAME_EXCEPTIONS,
    REGIONAL_FORMS,
)

logger = logging.getLogger(__name__)


def filter_pvp_forms(forms_df, pvp_forms=PVP_FORMS):
    """Keep only forms that are relevant to PvP (drop cosmetic-only forms)."""
    return forms_df[forms_df["form"].isin(pvp_forms)].copy()


def build_base_table(forms_df):
    """
    Rename pogoapi columns to our schema and add shadow-variant rows.

    Every Pokémon is treated as if it has a Shadow version. The
    "which Pokémon can actually be Shadow" pogoapi endpoint is outdated,
    so rather than under-report we generate a shadow row for everything.
    """
    pok_df = forms_df.rename(columns={"pokemon_id": "dex", "pokemon_name": "name"}).copy()

    # Normalize apostrophes (pogoapi uses a curly quote; damn you Farfetch'd).
    pok_df["name"] = pok_df["name"].str.replace("’", "'", regex=False)

    pok_df["shadow"] = False

    shadow_rows = pok_df.copy()
    shadow_rows["shadow"] = True

    pok_df = pd.concat([pok_df, shadow_rows], ignore_index=True)
    return pok_df.sort_values(["dex", "form", "shadow"]).reset_index(drop=True)


def build_pvpoke_names(pok_df):
    """Add the `pvpoke_name` column, matching PvPoke's display naming."""
    pok_df = pok_df.copy()

    pok_df["pvpoke_name"] = (
        pok_df["name"] + " (" + pok_df["form"].replace(FORM_SUFFIX).str.replace("_", " ") + ")"
    )

    # Base/no-suffix forms: just the species name.
    pok_df.loc[pok_df["form"].isin(["Normal", "Confined"]), "pvpoke_name"] = pok_df["name"]

    # Species whose pogoapi form has no PvP-relevant stat difference.
    pok_df.loc[pok_df["name"].isin(PVPOKE_FORM_EXCEPTIONS), "pvpoke_name"] = pok_df["name"]

    # One-off name overrides.
    pok_df["pvpoke_name"] = pok_df["pvpoke_name"].replace(PVPOKE_NAME_EXCEPTIONS)

    # Shadow suffix.
    pok_df["pvpoke_name"] = pok_df.apply(
        lambda row: f"{row['pvpoke_name']} (Shadow)" if row["shadow"] else row["pvpoke_name"],
        axis=1,
    )

    return pok_df


def apply_evo_ids(pok_df, evo_cache, evo_exceptions=EVO_EXCEPTIONS):
    """
    Add the `evo_ids` column from a {dex: [evo_ids...]} cache, applying
    per-form overrides where the naive evolution walk is wrong.
    """
    pok_df = pok_df.copy()
    pok_df["evo_ids"] = pok_df["dex"].map(evo_cache)

    def resolve(row):
        key = (row["dex"], row["form"])
        return evo_exceptions.get(key, row["evo_ids"])

    pok_df["evo_ids"] = pok_df.apply(resolve, axis=1)
    return pok_df


def _get_form_search_name(form):
    return REGIONAL_FORMS.get(form, form.lower())


def _make_search_string(dex, form, shadow, form_groups):
    forms = form_groups.get(dex, set())

    if len(forms) <= 1:
        form_string = ""
    elif form == "Normal":
        # Base form: exclude every regional variant.
        alternatives = forms - {"Normal"}
        form_string = "".join(
            f"&!{_get_form_search_name(f)}" for f in alternatives if f in REGIONAL_FORMS
        )
    elif form in REGIONAL_FORMS:
        form_string = f"&{_get_form_search_name(form)}"
    else:
        # Forms PvPoke distinguishes but Pokémon GO's search can't filter
        # on (e.g. Giratina Altered vs Origin, Kyurem Black vs White).
        form_string = ""

    form_string += "&shadow" if shadow else "&!shadow"
    return form_string


def build_search_strings(pok_df):
    """Add the `search_string` column used to filter the in-game Pokémon list."""
    pok_df = pok_df.copy()

    form_groups = pok_df.groupby("dex")["form"].apply(set).to_dict()

    pok_df["search_string"] = pok_df.apply(
        lambda row: ",".join(map(str, row["evo_ids"]))
        + _make_search_string(row["dex"], row["form"], row["shadow"], form_groups),
        axis=1,
    )

    return pok_df


def build_lookup_table(forms_df, evo_cache):
    """Run the full pipeline: raw forms_df + evo cache -> finished pok_df."""
    pok_df = filter_pvp_forms(forms_df)
    pok_df = build_base_table(pok_df)
    pok_df = build_pvpoke_names(pok_df)
    pok_df = apply_evo_ids(pok_df, evo_cache)
    pok_df = build_search_strings(pok_df)
    return pok_df


def find_unmatched(league_df, pok_df):
    """Rows in a league's rankings that have no matching pvpoke_name in pok_df."""
    merged = league_df.merge(
        pok_df,
        left_on=league_df["Pokemon"].str.lower(),
        right_on=pok_df["pvpoke_name"].str.lower(),
        how="left",
    )
    return merged[merged["pvpoke_name"].isna()]


def describe_unmatched(unmatched_df, pok_df):
    """Attach the pok_df entries for the same Dex, to help diagnose a mismatch."""
    df = unmatched_df.merge(pok_df, left_on="Dex", right_on="dex", how="left")
    return df[["Pokemon", "Dex", "pvpoke_name_y"]]
