 
import logging
import sys
from pathlib import Path
import re

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

logger = logging.getLogger(__name__)


def lookup_search_strings(names, pok_df, mode="PVP"):
    """
    Return a list of search strings for the given Pokémon names, matched
    against pok_df's pvpoke_name column (case-insensitive).
    """
    search_strings = []
 
    for name in names:
        
        if mode == "PVP":
            matches = pok_df.loc[
                pok_df["pvpoke_name"].str.lower() == name.lower(), "search_string"
            ]
        
        elif mode == "Raid":
            name = re.sub(r"^Mega ", "", name)
            name = re.sub(r" [XY]$", "", name)
            name = re.sub(r"^Primal ", "", name)
            
            
            matches = pok_df.loc[
                pok_df["dialgadex_name"].str.lower() == name.lower(), "search_string"
            ]
 
        if matches.empty:
            logger.warning("No match found for %s", name)
            continue
 
        search_string = matches.iloc[0]
 
        if not search_string:
            logger.warning("No search string for %s", name)
            continue
 
        search_strings.append(search_string)
 
    return search_strings

def parse_search_term(term):
    """
    Convert one search term such as:

        957,958,959&!shadow

    into groups:

        [
            {"957", "958", "959"},
            {"!shadow"},
        ]

    Each group represents an OR. The groups themselves are ANDed together.
    """
    groups = []

    for part in term.split("&"):
        # Commas represent OR
        options = frozenset(part.split(","))
        groups.append(options)

    return groups


def is_tautology(clause):
    """
    A clause containing both x and !x is always true.

    Example: {shadow, !shadow}
    """
    for literal in clause:
        if literal.startswith("!"):
            if literal[1:] in clause:
                return True
        else:
            if "!" + literal in clause:
                return True

    return False


def remove_redundant_clauses(clauses):
    """
    If clause A is a subset of clause B:

        A = {1, 2}
        B = {1, 2, 3}

    then B is redundant because A already covers it. (The 3 isn't missing
    from the final expression, but it's an optional way to satisfy the
    redundant second clause.)
    """
    # Remove duplicates and tautologies
    clauses = {frozenset(c) for c in clauses if not is_tautology(c)}

    # Smaller clauses are more useful, so check those first
    clauses = sorted(clauses, key=len)

    result = []

    for clause in clauses:
        # If an existing clause is a subset of this one, this clause is redundant.
        if not any(existing <= clause for existing in result):
            result.append(clause)

    return set(result)


def optimize_pokemon_search(search_terms):
    """
    Convert a list of parenthesized Pokémon GO search terms into one
    optimized Pokémon GO search string.

    Example input:

        [
            "957,958,959&!shadow",
            "37,38&!alola&shadow",
            "222&galar&!shadow",
        ]

    Returns a search string using only ',' and '&'.
    """
    # Each original term is one AND-expression.
    terms = [parse_search_term(term) for term in search_terms]

    # CNF starts with one empty clause.
    clauses = {frozenset()}

    for term in terms:
        new_clauses = set()

        # To convert (A AND B) OR (C AND D) we need:
        #   (A OR C) AND (A OR D) AND (B OR C) AND (B OR D)
        # so we combine every existing clause with every group from this term.
        for clause in clauses:
            for group in term:
                new_clause = clause | group

                if not is_tautology(new_clause):
                    new_clauses.add(frozenset(new_clause))

        # Remove redundant clauses after every step.
        clauses = remove_redundant_clauses(new_clauses)

    # Convert sets back into Pokémon GO syntax
    result = []

    for clause in clauses:
        literals = sorted(clause)  # deterministic output
        result.append(",".join(literals))

    # Sort primarily by length, then alphabetically
    result.sort(key=lambda x: (len(x), x))

    return "&".join(result)