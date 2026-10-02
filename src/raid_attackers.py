"""
Fetch and parse raid attacker rankings from DialgaDex (dialgadex.com).

DialgaDex's ranking table is built entirely client-side, so a plain
HTTP request returns only the app shell with no Pokémon data in it.
To read the table we render the page with Playwright (a headless
browser, so the site's own JavaScript actually runs and builds the
table), then hand the rendered HTML to BeautifulSoup to pull out the
ranked names.

Usage: See scripts/update_raid_attackers.py.
"""

import logging
import re
from datetime import date
from pathlib import Path
import pandas as pd

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from src.data_files import find_latest_file

logger = logging.getLogger(__name__)

# {type} is replaced with a value from RAID_TYPES. "Any" ranks the
# strongest attackers overall, with no type restriction.
TYPE_URL_TEMPLATE = "https://www.dialgadex.com/?strongest=&t={type}"

RAID_TYPES = [
    "Any", "Normal", "Fire", "Water", "Grass", "Electric", "Ice", "Fighting",
    "Poison", "Ground", "Flying", "Psychic", "Bug", "Rock", "Ghost",
    "Dragon", "Dark", "Steel", "Fairy",
]

# A ranked Pokémon's name sits in:
#   <td class="td-poke-name"><a...><span class="strongest-name">NAME</span></a></td>
NAME_SELECTOR = "td.td-poke-name span.strongest-name"
MOVE_SELECTOR = "span.type-text"

RAID_FILE_PATTERN = "raid_attackers_*.csv"

def render_page(url, ready_selector=NAME_SELECTOR, timeout_ms=15000):
    """Load a page with a real browser and return the fully rendered HTML."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")
        page.wait_for_selector(ready_selector, timeout=timeout_ms)
        html = page.content()
        browser.close()
    return html


def fetch_type_rankings(attacker_type, top_n=None):
    """Fetch and parse the raid attacker ranking for one type."""
    url = f"https://www.dialgadex.com/?strongest=&t={attacker_type}"

    logger.info("Rendering %s", url)

    html = render_page(url)

    return parse_ranking(
        html,
        attacker_type=attacker_type,
        top_n=top_n,
    )

def parse_ranking(html, attacker_type, top_n=None):
    """Extract ranked Pokémon, rank, moves and eDPS from rendered HTML."""
    soup = BeautifulSoup(html, "html.parser")

    rankings = []

    for row in soup.select("tr"):
        name_element = row.select_one(NAME_SELECTOR)
        if not name_element:
            continue
        
        form_element = row.select_one("span.poke-form-name")
        form = form_element.get_text(strip=True) if form_element else None
        
        form = (
        form_element.get_text(strip=True).strip("()")
        if form_element
        else None
)

        name = name_element.get_text(strip=True)
        if name.startswith("Shadow"):
            name = "Shadow " + name[len("Shadow"):].lstrip()
        

        # The first numeric <td> after the tier label is the rank.
        cells = row.select("td")

        # The rank is the second <td> in the example HTML.
        rank = None
        if len(cells) > 1:
            rank_text = cells[1].get_text(strip=True)
            if rank_text.isdigit():
                rank = int(rank_text)
                
        # Fast and charged moves
        moves = row.select(MOVE_SELECTOR)

        fast_move = moves[0].get_text(strip=True) if len(moves) > 0 else None
        charged_move = moves[1].get_text(strip=True) if len(moves) > 1 else None

        #eDPS
        edps = None
        for cell in cells:
            text = cell.get_text(" ", strip=True)

            if text.startswith("eDPS"):
                value = cell.find("b")
                if value:
                    edps = float(value.get_text(strip=True))
                break

        if rank is None or edps is None:
            continue

        rankings.append({
            "Type": attacker_type,
            "Rank": rank,
            "Pokemon": name,
            "Form": form,
            "Fast Move": fast_move,
            "Charged Move": charged_move,
            "eDPS": edps,
        })

    logger.info(
        "%s: found %d attackers before top_n limit",
        attacker_type,
        len(rankings),
    )

    if top_n:
        rankings = rankings[:top_n]

    return rankings

def save_raid_rankings(rankings, data_dir, on_date=None):
    """Save all type rankings to one dated CSV."""
    on_date = on_date or date.today()
    Path(data_dir).mkdir(parents=True, exist_ok=True)

    path = Path(data_dir) / f"raid_attackers_{on_date:%m_%d_%y}.csv"

    df = pd.DataFrame(rankings)
    df.to_csv(path, index=False)

    logger.info("Saved raid rankings to %s", path)
    return path


def load_raid_rankings(data_dir="data/raw/Dialgadex"):
    """Load the most recently saved raid rankings CSV as a DataFrame."""
    path = find_latest_file(RAID_FILE_PATTERN, data_dir)
    logger.info("Loading raid rankings from %s", path)
    return pd.read_csv(path)

def print_raid_rankings(rankings_df, top_n=10):
    """Print the top N attackers for each type."""
    types = sorted(rankings_df["Type"].unique())

    for attacker_type in types:
        type_df = (
            rankings_df[rankings_df["Type"] == attacker_type]
            .sort_values("Rank")
            .head(top_n)
        )

        if type_df.empty:
            logger.warning("No cached rankings found for type %s", attacker_type)
            continue

        print("=" * 20, f" {attacker_type} ", "=" * 20)

        print(type_df.to_string(index=False, columns=["Rank", "Pokemon", "Form", "Fast Move", "Charged Move", "eDPS"]))
        print()


def dump_rendered_html(attacker_type, out_path):
    """Save the fully rendered page to disk — useful if DialgaDex's markup changes."""
    url = TYPE_URL_TEMPLATE.format(type=attacker_type)
    logger.info("Rendering %s for inspection", url)

    html = render_page(url)
    Path(out_path).write_text(html, encoding="utf-8")
    logger.info("Saved rendered HTML to %s", out_path)
    return out_path
