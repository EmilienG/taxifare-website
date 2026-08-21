import base64
import math
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import folium
import requests
import streamlit as st
from branca.element import MacroElement, Template
from dotenv import load_dotenv
from streamlit_folium import st_folium
from streamlit_searchbox import st_searchbox

load_dotenv()

# ============================================================
# CONFIG
# ============================================================

st.set_page_config(
    page_title="TaxiFare — Fare Intelligence",
    page_icon="🚕",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Point to your FastAPI (optional endpoints live here).
# Override with TAXIFARE_API_URL in .env — e.g. Cloud Run URL without trailing slash.
# url = 'https://taxifare.lewagon.ai/predict'
# API_BASE = os.getenv("TAXIFARE_API_URL", "http://127.0.0.1:8000").rstrip("/")
API_BASE = os.getenv("TAXIFARE_API_URL", "https://taxifare.lewagon.ai").rstrip("/")
PREDICT_URL = f"{API_BASE}/predict"
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "").strip()

# Greater NYC (Manhattan, Brooklyn, Queens, Bronx, Staten Island, JFK, LGA).
NYC_BBOX = {
    "min_lat": 40.4774,
    "max_lat": 40.9176,
    "min_lon": -74.2591,
    "max_lon": -73.7004,
}
NYC_CENTER_LAT = 40.7128
NYC_CENTER_LON = -74.0060
NYC_SEARCH_RADIUS_M = 50_000
PHOTON_URL = "https://photon.komoot.io/api/"
PHOTON_REVERSE_URL = "https://photon.komoot.io/reverse"
GOOGLE_AUTOCOMPLETE_URL = (
    "https://maps.googleapis.com/maps/api/place/autocomplete/json"
)
GOOGLE_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"
GOOGLE_GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
GEOCODE_HEADERS = {"User-Agent": "TaxiFare-Website/1.0"}


def _searchbox_theme_style(
    bg: str, fg: str, muted: str, border: str, highlight: str
) -> dict:
    control = {
        "backgroundColor": bg,
        "border": f"1px solid {border}",
        "borderColor": border,
        "borderRadius": "12px",
        "color": fg,
        "WebkitTextFillColor": fg,
        "caretColor": fg,
        "boxShadow": "none",
        "minHeight": "42px",
        "cursor": "text",
        "&:hover": {"border": f"1px solid {border}"},
    }
    return {
        "wrapper": {
            "backgroundColor": "transparent",
            "color": fg,
            "width": "100%",
        },
        "dropdown": {
            "width": 0,
            "height": 0,
            "fill": "transparent",
            "stroke": "transparent",
        },
        "clear": {
            "icon": "cross",
            "clearable": "after-submit",
            "fill": muted,
            "stroke": muted,
            "width": 16,
            "height": 16,
        },
        "searchbox": {
            "optionEmpty": "hidden",
            "menuList": {
                "backgroundColor": bg,
                "color": fg,
                "borderRadius": "12px",
                "border": f"1px solid {border}",
                "padding": "6px",
                "marginTop": "6px",
                "boxShadow": "0 16px 40px rgba(0,0,0,0.22)",
            },
            "singleValue": {"display": "none"},
            "input": {
                "color": fg,
                "backgroundColor": "transparent",
                "WebkitTextFillColor": fg,
                "caretColor": fg,
            },
            "placeholder": {"color": muted, "WebkitTextFillColor": muted},
            "control": control,
            "option": {
                "color": fg,
                "backgroundColor": bg,
                "WebkitTextFillColor": fg,
                "highlightColor": highlight,
                "borderRadius": "8px",
                "cursor": "pointer",
                "padding": "8px 10px",
            },
        },
    }


SEARCHBOX_STYLE_LIGHT = _searchbox_theme_style(
    "#ffffff", "#161920", "#5c6572", "rgba(28,24,16,0.14)", "#c49212"
)
SEARCHBOX_STYLE_DARK = _searchbox_theme_style(
    "#0a0e14", "#f5f7fa", "#8d96a5", "rgba(255,255,255,0.09)", "#f7c948"
)
SEARCHBOX_STYLE_PRO = _searchbox_theme_style(
    "#151b2e", "#f4efe4", "#9aa3b5", "rgba(212,176,106,0.28)", "#d4b06a"
)

NYC_PRESETS = {
    "Times Square → JFK": {
        "pickup_latitude": 40.7580,
        "pickup_longitude": -73.9855,
        "dropoff_latitude": 40.6413,
        "dropoff_longitude": -73.7781,
        "passenger_count": 2,
    },
    "Brooklyn Bridge → Empire State": {
        "pickup_latitude": 40.7061,
        "pickup_longitude": -73.9969,
        "dropoff_latitude": 40.7484,
        "dropoff_longitude": -73.9857,
        "passenger_count": 1,
    },
    "Central Park → Wall Street": {
        "pickup_latitude": 40.7829,
        "pickup_longitude": -73.9654,
        "dropoff_latitude": 40.7074,
        "dropoff_longitude": -74.0113,
        "passenger_count": 3,
    },
    "SoHo → LaGuardia": {
        "pickup_latitude": 40.7233,
        "pickup_longitude": -74.0030,
        "dropoff_latitude": 40.7769,
        "dropoff_longitude": -73.8740,
        "passenger_count": 1,
    },
    "JFK → Times Square": {
        "pickup_latitude": 40.6413,
        "pickup_longitude": -73.7781,
        "dropoff_latitude": 40.7580,
        "dropoff_longitude": -73.9855,
        "passenger_count": 2,
    },
}

ASSETS_DIR = Path(__file__).resolve().parent / "assets" / "demo"

DEMO_IMAGES = [
    {
        "label": "Times Square",
        "filename": "times_square.jpg",
        "latitude": 40.7580,
        "longitude": -73.9855,
    },
    {
        "label": "JFK Airport",
        "filename": "jfk_airport.jpg",
        "latitude": 40.6413,
        "longitude": -73.7781,
    },
    {
        "label": "Brooklyn Bridge",
        "filename": "brooklyn_bridge.jpg",
        "latitude": 40.7061,
        "longitude": -73.9969,
    },
    {
        "label": "Central Park",
        "filename": "central_park.jpg",
        "latitude": 40.7829,
        "longitude": -73.9654,
    },
    {
        "label": "Empire State",
        "filename": "empire_state.jpg",
        "latitude": 40.7484,
        "longitude": -73.9857,
    },
    {
        "label": "Wall Street",
        "filename": "wall_street.jpg",
        "latitude": 40.7074,
        "longitude": -74.0113,
    },
    {
        "label": "SoHo",
        "filename": "soho.jpg",
        "latitude": 40.7233,
        "longitude": -74.0030,
    },
    {
        "label": "LaGuardia",
        "filename": "laguardia.jpg",
        "latitude": 40.7769,
        "longitude": -73.8740,
    },
    {
        "label": "Grand Central",
        "filename": "grand_central.jpg",
        "latitude": 40.7527,
        "longitude": -73.9772,
    },
    {
        "label": "One World Trade",
        "filename": "one_world_trade.jpg",
        "latitude": 40.7127,
        "longitude": -74.0134,
    },
    {
        "label": "Rockefeller",
        "filename": "rockefeller.jpg",
        "latitude": 40.7587,
        "longitude": -73.9787,
    },
    {
        "label": "Washington Sq.",
        "filename": "washington_square.jpg",
        "latitude": 40.7308,
        "longitude": -73.9973,
    },
    {
        "label": "Statue of Liberty",
        "filename": "statue_of_liberty.jpg",
        "latitude": 40.6892,
        "longitude": -74.0445,
    },
    {
        "label": "Flatiron",
        "filename": "flatiron.jpg",
        "latitude": 40.7411,
        "longitude": -73.9897,
    },
    {
        "label": "Chrysler",
        "filename": "chrysler.jpg",
        "latitude": 40.7516,
        "longitude": -73.9755,
    },
    {
        "label": "Hudson Yards",
        "filename": "hudson_yards.jpg",
        "latitude": 40.7538,
        "longitude": -74.0021,
    },
    {
        "label": "DUMBO",
        "filename": "dumbo.jpg",
        "latitude": 40.7033,
        "longitude": -73.9881,
    },
    {
        "label": "Guggenheim",
        "filename": "guggenheim.jpg",
        "latitude": 40.7830,
        "longitude": -73.9590,
    },
    {
        "label": "Coney Island",
        "filename": "coney_island.jpg",
        "latitude": 40.5755,
        "longitude": -73.9787,
    },
    {
        "label": "Bryant Park",
        "filename": "bryant_park.jpg",
        "latitude": 40.7536,
        "longitude": -73.9832,
    },
]

# ============================================================
# THEME
# ============================================================

THEMES = ("pro", "dark", "light")
DEFAULT_THEME = "pro"
THEME_LABELS = {
    "pro": "✨ Pro",
    "dark": "🌙 Nuit",
    "light": "☀️ Jour",
}
THEME_MAP_TILES = {
    "pro": "CartoDB dark_matter",
    "dark": "CartoDB dark_matter",
    "light": "CartoDB positron",
}
THEME_ROUTE_COLOR = {
    "pro": "#d4b06a",
    "dark": "#f7c948",
    "light": "#c49212",
}
SEARCHBOX_STYLES = {
    "pro": SEARCHBOX_STYLE_PRO,
    "dark": SEARCHBOX_STYLE_DARK,
    "light": SEARCHBOX_STYLE_LIGHT,
}


def init_theme() -> None:
    if "theme" not in st.session_state:
        requested = st.query_params.get("theme", DEFAULT_THEME)
        if isinstance(requested, list):
            requested = requested[0] if requested else DEFAULT_THEME
        st.session_state.theme = requested if requested in THEMES else DEFAULT_THEME


def cycle_theme() -> None:
    current = st.session_state.get("theme", DEFAULT_THEME)
    index = THEMES.index(current) if current in THEMES else 0
    st.session_state.theme = THEMES[(index + 1) % len(THEMES)]
    st.query_params["theme"] = st.session_state.theme


init_theme()

# ============================================================
# CSS — Pro (default), taxi night, warm daylight
# ============================================================

PRO_THEME_CSS = """
:root {
    color-scheme: dark;
    --bg: #0a0f1c;
    --bg-spot-1: rgba(212,176,106,0.16);
    --bg-spot-2: rgba(78,205,196,0.10);
    --bg-spot-3: rgba(124,108,232,0.10);
    --border: rgba(212,176,106,0.16);
    --text: #f4efe4;
    --muted: #9aa3b5;
    --yellow: #d4b06a;
    --green: #4ecdc4;
    --red: #e07a7a;
    --ink: #0a0f1c;
    --label: #c9d0de;
    --status-fg: #c9d0de;
    --status-bg: rgba(255,255,255,0.045);
    --dim: #7d8699;
    --input-bg: #151b2e;
    --input-fg: #f4efe4;
    --input-border: rgba(212,176,106,0.38);
    --input-ring: 0 0 0 1px rgba(212,176,106,0.08);
    --card-a: rgba(255,255,255,0.06);
    --card-b: rgba(16,22,40,0.72);
    --card-shadow: 0 22px 50px rgba(4,8,20,0.45), inset 0 1px 0 rgba(255,255,255,0.06);
    --price-glow: rgba(212,176,106,0.28);
    --price-fill: rgba(212,176,106,0.06);
    --price-border: rgba(212,176,106,0.28);
    --metric-bg: rgba(255,255,255,0.045);
    --metric-border: rgba(212,176,106,0.14);
    --btn-secondary-bg: rgba(255,255,255,0.05);
    --btn-secondary-border: rgba(212,176,106,0.22);
    --btn-secondary-hover: rgba(212,176,106,0.14);
    --scene-btn-bg: rgba(10, 15, 28, 0.92);
    --scene-btn-fg: #f4efe4;
    --scene-btn-border: rgba(212,176,106,0.18);
    --scene-card-border: rgba(212,176,106,0.18);
    --scene-card-bg: rgba(255,255,255,0.04);
    --footer: #6b7386;
    --scheme: dark;
    --btn-grad-a: #d4b06a;
    --btn-grad-b: #f0d7a2;
    --btn-shadow: rgba(212,176,106,0.22);
    --glow: rgba(212,176,106,0.45);
}
"""

DARK_THEME_CSS = """
:root {
    color-scheme: dark;
    --bg: #07090d;
    --bg-spot-1: rgba(247,201,72,0.10);
    --bg-spot-2: rgba(71,230,161,0.06);
    --bg-spot-3: rgba(247,201,72,0.04);
    --border: rgba(255,255,255,0.08);
    --text: #f5f7fa;
    --muted: #8d96a5;
    --yellow: #f7c948;
    --green: #47e6a1;
    --red: #ff6b7a;
    --ink: #0a0b0e;
    --label: #b7c0cc;
    --status-fg: #aab3c0;
    --status-bg: rgba(255,255,255,0.035);
    --dim: #707987;
    --input-bg: #0a0e14;
    --input-fg: #f5f7fa;
    --input-border: rgba(255,255,255,0.22);
    --input-ring: 0 0 0 1px rgba(255,255,255,0.04);
    --card-a: rgba(255,255,255,0.045);
    --card-b: rgba(255,255,255,0.015);
    --card-shadow: 0 18px 50px rgba(0,0,0,0.22), inset 0 1px 0 rgba(255,255,255,0.03);
    --price-glow: rgba(247,201,72,0.16);
    --price-fill: rgba(247,201,72,0.04);
    --price-border: rgba(247,201,72,0.16);
    --metric-bg: rgba(255,255,255,0.04);
    --metric-border: rgba(255,255,255,0.06);
    --btn-secondary-bg: rgba(255,255,255,0.06);
    --btn-secondary-border: rgba(255,255,255,0.09);
    --btn-secondary-hover: rgba(255,255,255,0.10);
    --scene-btn-bg: rgba(8, 10, 14, 0.92);
    --scene-btn-fg: #e8edf4;
    --scene-btn-border: rgba(255,255,255,0.08);
    --scene-card-border: rgba(255,255,255,0.08);
    --scene-card-bg: rgba(255,255,255,0.03);
    --footer: #4f5866;
    --scheme: dark;
    --btn-grad-a: #f7c948;
    --btn-grad-b: #ffdc73;
    --btn-shadow: rgba(247,201,72,0.14);
    --glow: rgba(247,201,72,0.45);
}
"""

LIGHT_THEME_CSS = """
:root {
    color-scheme: light;
    --bg: #f4f1e8;
    --bg-spot-1: rgba(247,201,72,0.28);
    --bg-spot-2: rgba(15,157,106,0.10);
    --bg-spot-3: rgba(247,201,72,0.12);
    --border: rgba(28,24,16,0.10);
    --text: #161920;
    --muted: #5c6572;
    --yellow: #c49212;
    --green: #0c8f61;
    --red: #d03a4c;
    --ink: #161920;
    --label: #3d4654;
    --status-fg: #3d4654;
    --status-bg: rgba(255,255,255,0.78);
    --dim: #6a7380;
    --input-bg: #ffffff;
    --input-fg: #161920;
    --input-border: #8a8376;
    --input-ring: 0 1px 2px rgba(28,24,16,0.08);
    --card-a: #ffffff;
    --card-b: #faf7f0;
    --card-shadow: 0 18px 40px rgba(40,30,10,0.08), inset 0 1px 0 rgba(255,255,255,0.95);
    --price-glow: rgba(247,201,72,0.32);
    --price-fill: #fffdf6;
    --price-border: rgba(196,146,18,0.28);
    --metric-bg: rgba(22,25,32,0.04);
    --metric-border: rgba(28,24,16,0.08);
    --btn-secondary-bg: #ffffff;
    --btn-secondary-border: rgba(28,24,16,0.12);
    --btn-secondary-hover: #fff6d8;
    --scene-btn-bg: #ffffff;
    --scene-btn-fg: #161920;
    --scene-btn-border: rgba(28,24,16,0.10);
    --scene-card-border: rgba(28,24,16,0.10);
    --scene-card-bg: #ffffff;
    --footer: #8b919c;
    --scheme: light;
    --btn-grad-a: #d4a017;
    --btn-grad-b: #f0c44a;
    --btn-shadow: rgba(196,146,18,0.20);
    --glow: rgba(196,146,18,0.35);
}
"""

THEME_CSS = {
    "pro": PRO_THEME_CSS,
    "dark": DARK_THEME_CSS,
    "light": LIGHT_THEME_CSS,
}

APP_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');

:root {
    color-scheme: dark;
    --bg: #0a0f1c;
    --bg-spot-1: rgba(212,176,106,0.16);
    --bg-spot-2: rgba(78,205,196,0.10);
    --bg-spot-3: rgba(124,108,232,0.10);
    --border: rgba(212,176,106,0.16);
    --text: #f4efe4;
    --muted: #9aa3b5;
    --yellow: #d4b06a;
    --green: #4ecdc4;
    --red: #e07a7a;
    --ink: #0a0f1c;
    --label: #c9d0de;
    --status-fg: #c9d0de;
    --status-bg: rgba(255,255,255,0.045);
    --dim: #7d8699;
    --input-bg: #151b2e;
    --input-fg: #f4efe4;
    --input-border: rgba(212,176,106,0.38);
    --input-ring: 0 0 0 1px rgba(212,176,106,0.08);
    --card-a: rgba(255,255,255,0.06);
    --card-b: rgba(16,22,40,0.72);
    --card-shadow: 0 22px 50px rgba(4,8,20,0.45), inset 0 1px 0 rgba(255,255,255,0.06);
    --price-glow: rgba(212,176,106,0.28);
    --price-fill: rgba(212,176,106,0.06);
    --price-border: rgba(212,176,106,0.28);
    --metric-bg: rgba(255,255,255,0.045);
    --metric-border: rgba(212,176,106,0.14);
    --btn-secondary-bg: rgba(255,255,255,0.05);
    --btn-secondary-border: rgba(212,176,106,0.22);
    --btn-secondary-hover: rgba(212,176,106,0.14);
    --scene-btn-bg: rgba(10, 15, 28, 0.92);
    --scene-btn-fg: #f4efe4;
    --scene-btn-border: rgba(212,176,106,0.18);
    --scene-card-border: rgba(212,176,106,0.18);
    --scene-card-bg: rgba(255,255,255,0.04);
    --footer: #6b7386;
    --space-1: 0.4rem;
    --space-2: 0.7rem;
    --space-3: 1rem;
    --space-4: 1.25rem;
    --radius: 18px;
    --radius-sm: 12px;
    --page-pad-x: 2rem;
    --page-pad-y: 1.2rem;
    --scheme: dark;
    --btn-grad-a: #d4b06a;
    --btn-grad-b: #f0d7a2;
    --btn-shadow: rgba(212,176,106,0.22);
    --glow: rgba(212,176,106,0.45);
}

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stMainBlockContainer"] {
    --st-background-color: var(--bg);
    --st-secondary-background-color: var(--input-bg);
    --st-text-color: var(--text);
    --st-heading-color: var(--text);
    --st-border-color: var(--border);
    --st-widget-border-color: var(--input-border);
    --st-primary-color: var(--yellow);
    --background-color: var(--bg);
    --secondary-background-color: var(--input-bg);
    --text-color: var(--text);
    color-scheme: var(--scheme);
    background:
        radial-gradient(circle at 12% 8%, var(--bg-spot-1), transparent 32%),
        radial-gradient(circle at 88% 12%, var(--bg-spot-2), transparent 30%),
        radial-gradient(circle at 50% 100%, var(--bg-spot-3), transparent 40%),
        var(--bg);
    color: var(--text);
}

.block-container,
[data-testid="stMainBlockContainer"] {
    max-width: 1320px;
    padding-top: var(--page-pad-y) !important;
    padding-bottom: 1.5rem !important;
    padding-left: var(--page-pad-x) !important;
    padding-right: var(--page-pad-x) !important;
}

#MainMenu, footer, header, [data-testid="stHeader"] { display: none !important; }

[data-testid="stVerticalBlock"] { gap: var(--space-2) !important; }
.block-container [data-testid="stElementContainer"] { margin-bottom: 0 !important; }
[data-testid="stWidgetLabel"] { margin-bottom: 0.25rem; }
[data-testid="stWidgetLabel"] p {
    font-size: 12px !important;
    font-weight: 600;
    color: var(--label) !important;
}
[data-testid="InputInstructions"] { display: none !important; }

/* One compact typeahead: iframe overlays so suggestions are not a 2nd field */
div[data-testid="stElementContainer"]:has(iframe[title="streamlit_searchbox.searchbox"]),
div[data-testid="element-container"]:has(iframe[title="streamlit_searchbox.searchbox"]) {
    position: relative !important;
    height: 44px !important;
    min-height: 44px !important;
    overflow: visible !important;
    z-index: 50;
}
div[data-testid="stElementContainer"]:has(.kicker-green) + div[data-testid="stElementContainer"],
div[data-testid="element-container"]:has(.kicker-green) + div[data-testid="element-container"] {
    z-index: 70 !important;
}
div[data-testid="stElementContainer"]:has(.kicker-red) + div[data-testid="stElementContainer"],
div[data-testid="element-container"]:has(.kicker-red) + div[data-testid="element-container"] {
    z-index: 60 !important;
}
div:has(> iframe[title="streamlit_searchbox.searchbox"]) {
    overflow: visible !important;
    height: 44px !important;
}
iframe[title="streamlit_searchbox.searchbox"] {
    position: absolute !important;
    top: 0;
    left: 0;
    width: 100% !important;
    min-height: 44px !important;
    background: transparent !important;
    border: none !important;
    color-scheme: var(--scheme);
    z-index: 1;
}
[data-testid="stCaptionContainer"] { margin-top: 0.15rem !important; }
[data-testid="stCaptionContainer"] p { font-size: 12px !important; color: var(--muted) !important; }

@keyframes fare-in {
    from { opacity: 0; transform: translateY(12px) scale(0.98); }
    to { opacity: 1; transform: translateY(0) scale(1); }
}
@keyframes glow-route {
    0%, 100% { filter: drop-shadow(0 0 4px var(--glow)); }
    50% { filter: drop-shadow(0 0 14px var(--glow)); }
}

div[data-testid="stHorizontalBlock"]:has(.brand) {
    align-items: center !important;
    margin: 0 0 var(--space-4);
    padding: 0 2px var(--space-3);
    border-bottom: 1px solid var(--border);
    gap: 0.75rem !important;
}
div[data-testid="stHorizontalBlock"]:has(.brand) [data-testid="stVerticalBlock"] {
    gap: 0.45rem !important;
}

.brand {
    display: flex; align-items: center;
    gap: 14px;
    margin: 0;
    padding: 0;
    min-height: 44px;
}
.brand-left { display: flex; align-items: center; gap: 12px; }
.logo {
    width: 42px; height: 42px; border-radius: 12px;
    background: linear-gradient(135deg, #f7c948, #ffdf78);
    display: flex; align-items: center; justify-content: center;
    color: #0a0b0e; font-size: 21px;
    box-shadow: 0 8px 24px rgba(247,201,72,0.25);
    animation: glow-route 3.2s ease-in-out infinite;
    flex-shrink: 0;
}
.brand-name {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 22px; font-weight: 700; letter-spacing: -0.5px; line-height: 1.1;
}
.brand-tag { color: var(--muted); font-size: 12px; margin-top: 3px; }

.section-head {
    display: flex; align-items: baseline; justify-content: space-between;
    gap: 10px 14px;
    margin: 0 0 0.2rem;
    flex-wrap: wrap;
}
.section-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 15px; font-weight: 600;
}
.section-sub { color: var(--muted); font-size: 12px; line-height: 1.35; }
.landmarks-head {
    margin-top: 0;
    margin-bottom: 0.45rem;
}
.kicker {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.3px;
    text-transform: uppercase;
    color: var(--muted);
    margin: 0.8rem 0 0.15rem;
}
.kicker-green { color: var(--green); margin-top: 0.35rem; }
.kicker-red { color: var(--red); }

div[data-testid="stHorizontalBlock"]:has(.main-panel) {
    align-items: stretch !important;
    gap: 1rem !important;
}

div[data-testid="stHorizontalBlock"]:has(.main-panel) > div {
    background: linear-gradient(145deg, var(--card-a), var(--card-b));
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.1rem 1.15rem 1.05rem !important;
    box-shadow: var(--card-shadow);
}

.price-card {
    margin-top: 0.25rem;
    padding: 1.15rem 0.75rem 0.85rem;
    border-radius: 14px;
    text-align: center;
    background:
        radial-gradient(circle at 80% 10%, var(--price-glow), transparent 42%),
        var(--price-fill);
    border: 1px solid var(--price-border);
    animation: fare-in 0.55s cubic-bezier(.2,.8,.2,1);
}
.price-label {
    color: var(--muted); font-size: 12px; text-transform: uppercase;
    letter-spacing: 1.8px; font-weight: 700;
}
.price {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 52px; line-height: 1; letter-spacing: -2px;
    font-weight: 700; color: var(--yellow); margin-top: 12px;
}
.price-note { color: var(--dim); font-size: 12px; margin-top: 10px; line-height: 1.4; }

.metric-row {
    display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; margin-top: 1rem;
}
.metric {
    background: var(--metric-bg);
    border: 1px solid var(--metric-border);
    border-radius: var(--radius-sm); padding: 11px 6px 10px;
    text-align: center;
    min-width: 0;
}
.metric-label {
    color: var(--dim); font-size: 10px; text-transform: uppercase; letter-spacing: 1.1px;
}
.metric-value {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 16px; font-weight: 600; margin-top: 5px;
}

.stButton > button {
    width: 100%; border: none; border-radius: 11px; min-height: 42px;
    background: linear-gradient(135deg, #f7c948, #ffdc73);
    color: #0a0b0e;
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700; font-size: 13px;
    transition: all 0.2s ease;
    box-shadow: 0 8px 22px rgba(247,201,72,0.14);
}
.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 14px 36px rgba(247,201,72,0.26);
}
.stButton > button[kind="secondary"],
.stButton > button[data-testid="baseButton-secondary"] {
    background: var(--btn-secondary-bg);
    color: var(--text);
    box-shadow: none;
    border: 1px solid var(--btn-secondary-border);
}
.stButton > button[kind="secondary"]:hover,
.stButton > button[data-testid="baseButton-secondary"]:hover {
    background: var(--btn-secondary-hover);
    box-shadow: none;
}

div[data-testid="stVerticalBlock"]:has(.theme-toggle-anchor) .stButton > button,
.st-key-theme_toggle button,
.st-key-theme_toggle [data-testid="stBaseButton-secondary"],
.st-key-theme_toggle [data-testid="baseButton-secondary"] {
    min-height: 42px;
    border-radius: 999px;
    background: var(--status-bg) !important;
    color: var(--status-fg) !important;
    border: 1px solid var(--border) !important;
    box-shadow: none !important;
    font-family: 'DM Sans', sans-serif;
    font-size: 12px;
    font-weight: 600;
}
div[data-testid="stVerticalBlock"]:has(.theme-toggle-anchor) .stButton > button:hover,
.st-key-theme_toggle button:hover {
    transform: none;
    background: var(--btn-secondary-hover) !important;
    box-shadow: none !important;
    border-color: var(--yellow) !important;
    color: var(--text) !important;
}

/* Native Streamlit widgets: always pair field background + readable text */
[data-testid="stNumberInput"],
[data-testid="stDateInput"],
[data-testid="stTimeInput"],
[data-testid="stSelectbox"],
[data-testid="stTextInput"] {
    width: 100%;
    color-scheme: var(--scheme);
}

[data-testid="stNumberInputContainer"],
[data-testid="stDateInput"] [data-baseweb="input"],
[data-testid="stDateInput"] [data-baseweb="input"] > div,
[data-testid="stTimeInput"] [data-baseweb="select"],
[data-testid="stTimeInput"] [data-baseweb="select"] > div,
[data-testid="stSelectbox"] [data-baseweb="select"],
[data-testid="stSelectbox"] [data-baseweb="select"] > div,
[data-testid="stTextInput"] [data-baseweb="input"],
[data-testid="stTextInput"] [data-baseweb="input"] > div,
[data-testid="stNumberInput"] [data-baseweb="input"] > div,
div[data-baseweb="input"],
div[data-baseweb="input"] > div,
div[data-baseweb="select"] > div,
div[data-baseweb="base-input"],
div[data-baseweb="base-input"] > div {
    background-color: var(--input-bg) !important;
    background: var(--input-bg) !important;
    color: var(--input-fg) !important;
    -webkit-text-fill-color: var(--input-fg) !important;
    border-color: var(--input-border) !important;
    border-width: 1.5px !important;
    border-style: solid !important;
    box-shadow: var(--input-ring, none) !important;
    border-radius: var(--radius-sm) !important;
    min-height: 42px;
    caret-color: var(--input-fg) !important;
    color-scheme: var(--scheme);
}

[data-testid="stNumberInputField"],
[data-testid="stDateInputField"],
[data-testid="stTimeInputTimeDisplay"],
[data-testid="stNumberInput"] input,
[data-testid="stDateInput"] input,
[data-testid="stTimeInput"] input,
[data-testid="stSelectbox"] input,
[data-testid="stTextInput"] input,
[data-testid="stTimeInput"] [data-baseweb="select"] span,
[data-testid="stTimeInput"] [data-baseweb="select"] div,
[data-testid="stSelectbox"] [data-baseweb="select"] span,
[data-testid="stSelectbox"] [data-baseweb="select"] div,
input, textarea, select {
    color: var(--input-fg) !important;
    -webkit-text-fill-color: var(--input-fg) !important;
    background-color: var(--input-bg) !important;
    caret-color: var(--input-fg) !important;
    color-scheme: var(--scheme);
}

[data-testid="stNumberInputStepDown"],
[data-testid="stNumberInputStepUp"] {
    color: var(--input-fg) !important;
    background: var(--input-bg) !important;
}
[data-testid="stNumberInputStepDown"] svg,
[data-testid="stNumberInputStepUp"] svg,
[data-testid="stTimeInput"] svg,
[data-testid="stDateInput"] svg,
[data-testid="stSelectbox"] svg {
    fill: var(--muted) !important;
    stroke: var(--muted) !important;
    color: var(--muted) !important;
}

input::placeholder, textarea::placeholder,
[data-baseweb="select"] [class*="placeholder"],
[data-baseweb="input"] [class*="placeholder"] {
    color: var(--muted) !important;
    -webkit-text-fill-color: var(--muted) !important;
    opacity: 1 !important;
}

input:-webkit-autofill,
input:-webkit-autofill:hover,
input:-webkit-autofill:focus {
    -webkit-text-fill-color: var(--input-fg) !important;
    caret-color: var(--input-fg) !important;
    box-shadow: 0 0 0 1000px var(--input-bg) inset !important;
    transition: background-color 9999s ease-out;
}

[data-baseweb="popover"],
[data-baseweb="menu"],
[data-baseweb="popover"] ul,
[data-baseweb="popover"] li,
[data-baseweb="popover"] div,
ul[role="listbox"],
li[role="option"] {
    background-color: var(--input-bg) !important;
    color: var(--input-fg) !important;
    -webkit-text-fill-color: var(--input-fg) !important;
}

.trip-meta { height: 0; overflow: hidden; }
div[data-testid="stVerticalBlock"]:has(.trip-meta) [data-testid="stWidgetLabel"] p {
    font-size: 13px !important;
    font-weight: 700 !important;
    color: var(--label) !important;
    letter-spacing: 0.02em;
}
div[data-testid="stVerticalBlock"]:has(.trip-meta) [data-testid="stDateInputField"],
div[data-testid="stVerticalBlock"]:has(.trip-meta) [data-testid="stTimeInputTimeDisplay"],
div[data-testid="stVerticalBlock"]:has(.trip-meta) [data-testid="stSelectbox"] span,
div[data-testid="stVerticalBlock"]:has(.trip-meta) [data-testid="stNumberInputField"] {
    font-size: 15px !important;
    font-weight: 650 !important;
    font-variant-numeric: tabular-nums;
    letter-spacing: 0.2px;
}
div[data-testid="stVerticalBlock"]:has(.trip-meta) [data-testid="stTimeInputClearButton"] {
    display: none !important;
}
div[data-testid="stVerticalBlock"]:has(.trip-meta) [data-testid="stTimeInputTimeDisplay"] {
    max-width: none !important;
    overflow: visible !important;
    text-overflow: clip !important;
    white-space: nowrap !important;
}
div[data-testid="stVerticalBlock"]:has(.trip-meta) [data-baseweb="select"] > div,
div[data-testid="stVerticalBlock"]:has(.trip-meta) [data-baseweb="input"] > div {
    min-height: 46px !important;
    padding-left: 0.7rem !important;
    padding-right: 0.5rem !important;
}

.scene-carousel {
    overflow: hidden;
    margin: 0 0 1.15rem;
    max-width: 100%;
    -webkit-mask-image: linear-gradient(to right, transparent 0, #000 24px, #000 calc(100% - 24px), transparent 100%);
    mask-image: linear-gradient(to right, transparent 0, #000 24px, #000 calc(100% - 24px), transparent 100%);
}
.scene-track {
    display: flex;
    width: max-content;
    animation: scene-marquee 48s linear infinite;
    will-change: transform;
}
.scene-group {
    display: flex;
    gap: 0.7rem;
    padding-right: 0.7rem;
}
.scene-carousel:hover .scene-track,
.scene-carousel:focus-within .scene-track {
    animation-play-state: paused;
}
@keyframes scene-marquee {
    from { transform: translateX(0); }
    to { transform: translateX(-50%); }
}
.scene-card {
    position: relative;
    display: block;
    flex: 0 0 172px;
    width: 172px;
    border-radius: var(--radius-sm);
    overflow: hidden;
    line-height: 0;
    border: 2px solid var(--scene-card-border);
    background: var(--scene-card-bg);
    text-decoration: none;
    color: inherit;
    cursor: pointer;
}
a.scene-card,
a.scene-card:hover,
a.scene-card:visited {
    color: inherit;
    text-decoration: none;
}
.scene-card img {
    width: 100%;
    height: 118px;
    object-fit: cover;
    display: block;
    filter: saturate(1.05) contrast(1.04);
    transition: transform 0.25s ease, filter 0.25s ease;
}
.scene-card:hover img {
    transform: scale(1.05);
    filter: saturate(1.12) contrast(1.06) brightness(1.06);
}
.scene-caption {
    position: absolute;
    left: 0; right: 0; bottom: 0;
    padding: 28px 10px 8px;
    background: linear-gradient(transparent 0%, rgba(0,0,0,0.58) 40%, rgba(0,0,0,0.92) 100%);
    color: #fff;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: -0.15px;
    line-height: 1.2;
    white-space: normal;
    word-break: break-word;
    text-shadow: 0 1px 2px rgba(0,0,0,0.85);
    pointer-events: none;
    z-index: 1;
}
.scene-badge {
    position: absolute;
    top: 8px;
    left: 8px;
    z-index: 2;
    padding: 4px 8px;
    border-radius: 999px;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.4px;
    text-transform: uppercase;
    line-height: 1.3;
    pointer-events: none;
}
.scene-card.pickup {
    border-color: var(--green);
    box-shadow: 0 0 16px rgba(71,230,161,0.28);
}
.scene-card.pickup .scene-badge {
    background: var(--green);
    color: #0a0b0e;
}
.scene-card.dropoff {
    border-color: var(--red);
    box-shadow: 0 0 16px rgba(255,107,122,0.28);
}
.scene-card.dropoff .scene-badge {
    background: var(--red);
    color: #fff;
}

.footer {
    text-align: center;
    margin-top: var(--space-4);
    padding-top: var(--space-3);
    border-top: 1px solid var(--border);
    color: var(--footer);
    font-size: 11px;
    line-height: 1.5;
}
.footer span { color: var(--yellow); }

iframe { border-radius: 14px; }
iframe[title*="folium"] { min-height: 280px; }

@media (max-width: 1100px) {
    :root { --page-pad-x: 1.2rem; }
    .price { font-size: 44px; }

    div[data-testid="stHorizontalBlock"]:has(.main-panel) {
        flex-direction: column !important;
        flex-wrap: nowrap !important;
        align-items: stretch !important;
        gap: 0.9rem !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.main-panel) > div,
    div[data-testid="stHorizontalBlock"]:has(.main-panel) > [data-testid="stColumn"],
    div[data-testid="stHorizontalBlock"]:has(.main-panel) > [data-testid="column"] {
        flex: 1 1 auto !important;
        width: 100% !important;
        min-width: 0 !important;
        max-width: 100% !important;
    }

    .scene-card { flex-basis: 160px; width: 160px; }
    .scene-card img { height: 110px; }
    .scene-caption { font-size: 12.5px; }
}

@media (max-width: 700px) {
    :root { --page-pad-x: 0.9rem; --page-pad-y: 0.85rem; }

    .block-container,
    [data-testid="stMainBlockContainer"] {
        padding-left: max(0.9rem, env(safe-area-inset-left)) !important;
        padding-right: max(0.9rem, env(safe-area-inset-right)) !important;
        padding-bottom: 1.25rem !important;
    }

    [data-testid="stVerticalBlock"] { gap: 0.55rem !important; }

    div[data-testid="stHorizontalBlock"]:has(.brand) {
        flex-direction: column !important;
        align-items: stretch !important;
        gap: 0.65rem !important;
        margin-bottom: 0.9rem;
        padding-bottom: 0.85rem;
    }
    div[data-testid="stHorizontalBlock"]:has(.brand) > div {
        width: 100% !important;
        min-width: 0 !important;
        flex: 1 1 100% !important;
    }

    .logo { width: 38px; height: 38px; font-size: 19px; border-radius: 11px; }
    .brand-name { font-size: 20px; }

    .section-head {
        flex-direction: column;
        align-items: flex-start;
        gap: 3px;
        margin-bottom: 0.15rem;
    }

    div[data-testid="stHorizontalBlock"]:has(.main-panel) > div {
        border-radius: 16px;
        padding: 0.95rem 0.9rem 0.9rem !important;
    }

    .price { font-size: 40px; letter-spacing: -1.5px; margin-top: 10px; }
    .price-card { padding: 1rem 0.6rem 0.75rem; }
    .metric-row { gap: 6px; margin-top: 0.85rem; }
    .metric { padding: 9px 4px 8px; }
    .metric-value { font-size: 14px; }
    .metric-label { font-size: 9px; }

    .scene-group { gap: 0.55rem; padding-right: 0.55rem; }
    .scene-card { flex-basis: 148px; width: 148px; }
    .scene-card img { height: 100px; }
    .scene-caption { font-size: 12px; padding: 24px 8px 7px; }
    .landmarks-head { margin-top: 0; }

    iframe[title*="folium"] { height: 260px !important; min-height: 240px; }
    iframe { border-radius: 12px; }

    .kicker { margin-top: 0.75rem; }
    .kicker-green { margin-top: 0.25rem; }
    .footer { margin-top: 1rem; padding-top: 0.8rem; }
}

@media (max-width: 420px) {
    .brand-tag { font-size: 11px; }
    .price { font-size: 34px; letter-spacing: -1px; }
    .metric-row { grid-template-columns: 1fr; }

    div[data-testid="stColumn"]:has(.kicker-green) [data-testid="stHorizontalBlock"] {
        flex-wrap: wrap !important;
        gap: 0.55rem !important;
    }
    div[data-testid="stColumn"]:has(.kicker-green) [data-testid="stHorizontalBlock"] > div,
    div[data-testid="column"]:has(.kicker-green) [data-testid="stHorizontalBlock"] > div {
        flex: 1 1 100% !important;
        width: 100% !important;
        min-width: 100% !important;
    }

    .scene-card { flex-basis: 136px; width: 136px; }
}

@media (prefers-reduced-motion: reduce) {
    .scene-track { animation: none; }
    .scene-carousel {
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        scrollbar-width: none;
        -webkit-mask-image: none;
        mask-image: none;
    }
    .scene-carousel::-webkit-scrollbar { display: none; }
    .scene-group + .scene-group { display: none; }
}
</style>
"""


# ============================================================
# HELPERS
# ============================================================

def in_nyc_bbox(lat: float, lon: float) -> bool:
    return (
        NYC_BBOX["min_lat"] <= lat <= NYC_BBOX["max_lat"]
        and NYC_BBOX["min_lon"] <= lon <= NYC_BBOX["max_lon"]
    )


def _photon_label(props: dict) -> str:
    parts: list[str] = []
    name = props.get("name")
    housenumber = props.get("housenumber")
    street = props.get("street")
    if housenumber and street:
        parts.append(f"{housenumber} {street}")
    elif street:
        parts.append(street)
    if name and name not in parts:
        parts.insert(0, name)
    for key in ("district", "city", "state"):
        value = props.get(key)
        if value and value not in parts:
            parts.append(value)
    return ", ".join(parts) if parts else "New York"


def google_autocomplete(query: str) -> list[tuple[str, dict]]:
    response = requests.get(
        GOOGLE_AUTOCOMPLETE_URL,
        params={
            "input": query,
            "key": GOOGLE_PLACES_API_KEY,
            "language": "en",
            "components": "country:us",
            "location": f"{NYC_CENTER_LAT},{NYC_CENTER_LON}",
            "radius": NYC_SEARCH_RADIUS_M,
            "strictbounds": "true",
        },
        timeout=6,
    )
    response.raise_for_status()
    data = response.json()
    status = data.get("status")
    if status not in ("OK", "ZERO_RESULTS"):
        raise RuntimeError(data.get("error_message") or status or "GOOGLE_ERROR")
    results: list[tuple[str, dict]] = []
    for pred in data.get("predictions") or []:
        label = pred.get("description") or ""
        place_id = pred.get("place_id")
        if not label or not place_id:
            continue
        results.append(
            (label, {"source": "google", "place_id": place_id, "label": label})
        )
    return results


def photon_search(query: str) -> list[tuple[str, dict]]:
    bbox = (
        f"{NYC_BBOX['min_lon']},{NYC_BBOX['min_lat']},"
        f"{NYC_BBOX['max_lon']},{NYC_BBOX['max_lat']}"
    )
    response = requests.get(
        PHOTON_URL,
        params={"q": query, "limit": 8, "lang": "en", "bbox": bbox},
        headers=GEOCODE_HEADERS,
        timeout=6,
    )
    response.raise_for_status()
    results: list[tuple[str, dict]] = []
    for feat in response.json().get("features") or []:
        coords = (feat.get("geometry") or {}).get("coordinates") or []
        if len(coords) < 2:
            continue
        lon, lat = float(coords[0]), float(coords[1])
        if not in_nyc_bbox(lat, lon):
            continue
        label = _photon_label(feat.get("properties") or {})
        results.append(
            (label, {"source": "photon", "lat": lat, "lon": lon, "label": label})
        )
    return results


def google_reverse_geocode(lat: float, lon: float) -> Optional[str]:
    response = requests.get(
        GOOGLE_GEOCODE_URL,
        params={
            "latlng": f"{lat},{lon}",
            "key": GOOGLE_PLACES_API_KEY,
            "language": "en",
        },
        timeout=6,
    )
    response.raise_for_status()
    data = response.json()
    if data.get("status") not in ("OK", "ZERO_RESULTS"):
        raise RuntimeError(data.get("error_message") or data.get("status") or "GOOGLE_ERROR")
    for result in data.get("results") or []:
        label = (result.get("formatted_address") or "").strip()
        if label:
            return label
    return None


def photon_reverse_geocode(lat: float, lon: float) -> Optional[str]:
    response = requests.get(
        PHOTON_REVERSE_URL,
        params={"lat": lat, "lon": lon, "lang": "en", "limit": 1},
        headers=GEOCODE_HEADERS,
        timeout=6,
    )
    response.raise_for_status()
    features = response.json().get("features") or []
    if not features:
        return None
    label = _photon_label(features[0].get("properties") or {})
    return label or None


@st.cache_data(ttl=3600)
def reverse_geocode(lat: float, lon: float) -> str:
    lat, lon = round(float(lat), 5), round(float(lon), 5)
    if GOOGLE_PLACES_API_KEY:
        try:
            label = google_reverse_geocode(lat, lon)
            if label:
                return label
        except Exception:
            pass
    try:
        label = photon_reverse_geocode(lat, lon)
        if label:
            return label
    except Exception:
        pass
    return f"{lat:.5f}, {lon:.5f}"


def search_nyc_places(searchterm: str) -> list[tuple[str, dict]]:
    query = (searchterm or "").strip()
    if len(query) < 2:
        return []
    if GOOGLE_PLACES_API_KEY:
        try:
            results = google_autocomplete(query)
            if results:
                return results
        except Exception:
            pass
    try:
        return photon_search(query)
    except Exception:
        return []


def google_place_details(place_id: str) -> Optional[dict]:
    response = requests.get(
        GOOGLE_DETAILS_URL,
        params={
            "place_id": place_id,
            "fields": "geometry,formatted_address,name",
            "key": GOOGLE_PLACES_API_KEY,
            "language": "en",
        },
        timeout=6,
    )
    response.raise_for_status()
    data = response.json()
    if data.get("status") != "OK":
        return None
    result = data.get("result") or {}
    loc = (result.get("geometry") or {}).get("location") or {}
    lat, lon = loc.get("lat"), loc.get("lng")
    if lat is None or lon is None:
        return None
    return {
        "lat": float(lat),
        "lon": float(lon),
        "label": result.get("formatted_address") or result.get("name"),
    }


def resolve_place(payload: dict) -> Optional[dict]:
    source = payload.get("source")
    if source == "google":
        place_id = payload.get("place_id")
        if not place_id:
            return None
        try:
            return google_place_details(place_id)
        except Exception:
            return None
    if source == "photon":
        lat, lon = payload.get("lat"), payload.get("lon")
        if lat is None or lon is None:
            return None
        return {
            "lat": float(lat),
            "lon": float(lon),
            "label": payload.get("label"),
        }
    return None


def _address_search_key(target: str) -> str:
    theme = st.session_state.get("theme", DEFAULT_THEME)
    return f"{target}_address_search_{theme}"


def set_address_field(target: str, label: str) -> None:
    """Show `label` in the address searchbox by remounting the React component."""
    text = (label or "").strip()
    st.session_state[f"{target}_address_label"] = text
    key = _address_search_key(target)
    st.session_state[key] = {
        "result": None,
        "search": text,
        "options_js": [],
        "options_py": [],
        "key_react": f"{key}_react_{time.time()}",
    }


def apply_selected_place(payload: Any, target: str) -> None:
    if not isinstance(payload, dict):
        return
    identity = payload.get("place_id") or (
        payload.get("lat"),
        payload.get("lon"),
        payload.get("label"),
    )
    last_key = f"last_{target}_place"
    if st.session_state.get(last_key) == identity:
        return
    place = resolve_place(payload)
    if not place:
        return
    lat, lon = place["lat"], place["lon"]
    if not in_nyc_bbox(lat, lon):
        return
    if target == "pickup":
        st.session_state.pickup_latitude = lat
        st.session_state.pickup_longitude = lon
        st.session_state.photo_pickup = None
    else:
        st.session_state.dropoff_latitude = lat
        st.session_state.dropoff_longitude = lon
        st.session_state.photo_dropoff = None
    st.session_state[last_key] = identity
    st.session_state.map_fit_route = True
    if place.get("label"):
        st.session_state[f"{target}_address_label"] = place["label"]


def render_address_search(target: str, placeholder: str) -> None:
    style = SEARCHBOX_STYLES.get(
        st.session_state.get("theme", DEFAULT_THEME), SEARCHBOX_STYLE_PRO
    )
    selected = st_searchbox(
        search_nyc_places,
        placeholder=placeholder,
        key=_address_search_key(target),
        debounce=250,
        edit_after_submit="option",
        style_overrides=style,
        default_searchterm=st.session_state.get(f"{target}_address_label", "") or "",
        submit_function=lambda payload, t=target: apply_selected_place(payload, t),
    )
    apply_selected_place(selected, target)


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def place_by_filename(filename: Optional[str]) -> Optional[dict]:
    if not filename:
        return None
    return next((d for d in DEMO_IMAGES if d["filename"] == filename), None)


def load_preset(preset_name: str) -> None:
    st.session_state.preset_key = preset_name
    trip = NYC_PRESETS[preset_name]
    for k, v in trip.items():
        st.session_state[k] = v
    st.session_state.photo_pickup = None
    st.session_state.photo_dropoff = None
    st.session_state.map_fit_route = True


def on_preset_change() -> None:
    load_preset(st.session_state.preset_key)


def consume_photo_click() -> None:
    """Apply a landmark chosen from the photo grid."""
    raw = st.query_params.get("place")
    if not raw:
        return
    filename = raw[0] if isinstance(raw, list) else raw
    try:
        del st.query_params["place"]
    except KeyError:
        pass
    demo = place_by_filename(filename)
    if demo:
        queue_photo_point(demo)


def queue_photo_point(demo: dict) -> None:
    """First photo = pickup, second = dropoff. A third click starts a new trip."""
    fname = demo["filename"]
    pickup = st.session_state.get("photo_pickup")
    dropoff = st.session_state.get("photo_dropoff")

    if pickup == fname:
        st.session_state.photo_pickup = None
        st.session_state.photo_dropoff = None
        return
    if dropoff == fname:
        st.session_state.photo_dropoff = None
        return

    pending = {}
    if not pickup:
        st.session_state.photo_pickup = fname
        pending["pickup"] = demo
    elif not dropoff:
        st.session_state.photo_dropoff = fname
        pending["dropoff"] = demo
    else:
        st.session_state.photo_pickup = fname
        st.session_state.photo_dropoff = None
        pending["pickup"] = demo

    st.session_state.pending_photo_points = pending


def apply_pending_photo_points() -> None:
    """Load photo pickup/dropoff into coordinate widgets before they mount."""
    pending = st.session_state.pop("pending_photo_points", None)
    if not pending:
        return

    if "pickup" in pending:
        place = pending["pickup"]
        st.session_state.pickup_latitude = place["latitude"]
        st.session_state.pickup_longitude = place["longitude"]
        set_address_field("pickup", place["label"])
    if "dropoff" in pending:
        place = pending["dropoff"]
        st.session_state.dropoff_latitude = place["latitude"]
        st.session_state.dropoff_longitude = place["longitude"]
        set_address_field("dropoff", place["label"])
    st.session_state.map_fit_route = True

    pickup = place_by_filename(st.session_state.get("photo_pickup"))
    dropoff = place_by_filename(st.session_state.get("photo_dropoff"))
    if pickup and dropoff:
        match = next(
            (
                name
                for name, trip in NYC_PRESETS.items()
                if abs(trip["pickup_latitude"] - pickup["latitude"]) < 0.0008
                and abs(trip["pickup_longitude"] - pickup["longitude"]) < 0.0008
                and abs(trip["dropoff_latitude"] - dropoff["latitude"]) < 0.0008
                and abs(trip["dropoff_longitude"] - dropoff["longitude"]) < 0.0008
            ),
            None,
        )
        if match:
            st.session_state.preset_key = match


def apply_pending_map_click() -> None:
    """Apply a marker drag queued on the previous run, before coordinate widgets mount."""
    pending = st.session_state.pop("pending_map_click", None)
    if not pending:
        return

    lat, lon = pending["lat"], pending["lon"]
    address = reverse_geocode(lat, lon)
    if pending["target"] == "pickup":
        st.session_state.pickup_latitude = lat
        st.session_state.pickup_longitude = lon
        st.session_state.photo_pickup = None
        set_address_field("pickup", address)
    else:
        st.session_state.dropoff_latitude = lat
        st.session_state.dropoff_longitude = lon
        st.session_state.photo_dropoff = None
        set_address_field("dropoff", address)


class _DragEndClick(MacroElement):
    """After a marker is dropped, emit a click so streamlit-folium returns the new lat/lng."""

    _template = Template(
        """
        {% macro script(this, kwargs) %}
        {{ this._parent.get_name() }}.on("dragend", function(e) {
            var ll = e.target.getLatLng();
            e.target.fire("click", {
                latlng: ll,
                sourceTarget: e.target,
                target: e.target
            });
        });
        {% endmacro %}
        """
    )


def _draggable_marker(lat: float, lon: float, label: str, color: str) -> folium.Marker:
    marker = folium.Marker(
        [lat, lon],
        tooltip=label,
        popup=f"{label}<br>{lat:.5f}, {lon:.5f}",
        icon=folium.Icon(color=color, icon="info-sign"),
        draggable=True,
    )
    marker.add_child(_DragEndClick())
    return marker


def _drag_target(map_data: Optional[dict]) -> Optional[str]:
    tooltip = ((map_data or {}).get("last_object_clicked_tooltip") or "").strip()
    popup = ((map_data or {}).get("last_object_clicked_popup") or "").strip()
    label = tooltip or popup
    if "Départ" in label:
        return "pickup"
    if "Arrivée" in label:
        return "dropoff"
    return None


def render_clickable_route_map(
    pickup_lat: float,
    pickup_lon: float,
    dropoff_lat: float,
    dropoff_lon: float,
) -> None:
    """Pickup and dropoff pins can be dragged directly on the map."""
    fit_route = bool(st.session_state.pop("map_fit_route", False))
    center_lat = (pickup_lat + dropoff_lat) / 2
    center_lon = (pickup_lon + dropoff_lon) / 2

    theme_key = st.session_state.get("theme", DEFAULT_THEME)
    tiles = THEME_MAP_TILES.get(theme_key, "CartoDB dark_matter")
    route_color = THEME_ROUTE_COLOR.get(theme_key, "#d4b06a")
    # Keep the base map script stable so dragging does not remount / reset the view.
    route_map = folium.Map(
        location=[NYC_CENTER_LAT, NYC_CENTER_LON],
        zoom_start=11,
        tiles=tiles,
    )

    points = folium.FeatureGroup(name="points")
    _draggable_marker(pickup_lat, pickup_lon, "Départ", "green").add_to(points)
    _draggable_marker(dropoff_lat, dropoff_lon, "Arrivée", "red").add_to(points)
    folium.PolyLine(
        [[pickup_lat, pickup_lon], [dropoff_lat, dropoff_lon]],
        color=route_color,
        weight=4,
        opacity=0.85,
    ).add_to(points)

    map_data = st_folium(
        route_map,
        feature_group_to_add=points,
        center=[center_lat, center_lon] if fit_route else None,
        zoom=11 if fit_route else None,
        width=None,
        height=360,
        returned_objects=[
            "last_object_clicked",
            "last_object_clicked_tooltip",
            "last_object_clicked_popup",
        ],
        key=f"route_map_clicker_{st.session_state.get('theme', DEFAULT_THEME)}",
        use_container_width=True,
    )

    clicked = (map_data or {}).get("last_object_clicked")
    target = _drag_target(map_data)
    if not clicked or not target:
        return

    lat, lon = float(clicked["lat"]), float(clicked["lng"])
    drag_key = (target, round(lat, 5), round(lon, 5))
    if drag_key == st.session_state.get("last_map_drag"):
        return

    current_lat = pickup_lat if target == "pickup" else dropoff_lat
    current_lon = pickup_lon if target == "pickup" else dropoff_lon
    if abs(current_lat - lat) < 1e-5 and abs(current_lon - lon) < 1e-5:
        return

    st.session_state.last_map_drag = drag_key
    st.session_state.pending_map_click = {"target": target, "lat": lat, "lon": lon}
    st.rerun()


@st.cache_data
def place_image_uri(filename: str) -> str:
    data = (ASSETS_DIR / filename).read_bytes()
    return f"data:image/jpeg;base64,{base64.b64encode(data).decode()}"


def scene_card_html(demo: dict, theme: str) -> str:
    fname = demo["filename"]
    label = (
        demo["label"]
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
    if st.session_state.get("photo_pickup") == fname:
        frame = "pickup"
        badge = '<div class="scene-badge">Départ</div>'
    elif st.session_state.get("photo_dropoff") == fname:
        frame = "dropoff"
        badge = '<div class="scene-badge">Arrivée</div>'
    else:
        frame = ""
        badge = ""
    return (
        f'<a class="scene-card {frame}" href="?theme={theme}&amp;place={fname}" '
        f'target="_self">'
        f'<img src="{place_image_uri(fname)}" alt="{label}">'
        f"{badge}"
        f'<div class="scene-caption">{label}</div>'
        f"</a>"
    )


def render_photo_scenes() -> None:
    """Photos are places: first click sets pickup, second sets dropoff."""
    if "photo_pickup" not in st.session_state:
        st.session_state.photo_pickup = None
        st.session_state.photo_dropoff = None

    theme = st.session_state.get("theme", DEFAULT_THEME)
    cards = "".join(scene_card_html(demo, theme) for demo in DEMO_IMAGES)
    st.markdown(
        f"""
<div class="section-head landmarks-head">
  <div class="section-title">Lieux emblématiques</div>
</div>
<div class="scene-carousel">
  <div class="scene-track">
    <div class="scene-group">{cards}</div>
    <div class="scene-group" aria-hidden="true">{cards}</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def predict_one(trip: dict, timeout: int = 20) -> float:
    r = requests.get(PREDICT_URL, params=trip, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, dict) and "fare" in data:
        return float(data["fare"])
    raise ValueError(f"Unexpected API payload: {data}")


def trip_payload(dt: datetime, lon_p, lat_p, lon_d, lat_d, passengers: int) -> dict:
    return {
        "pickup_datetime": dt.strftime("%Y-%m-%d %H:%M:%S"),
        "pickup_longitude": float(lon_p),
        "pickup_latitude": float(lat_p),
        "dropoff_longitude": float(lon_d),
        "dropoff_latitude": float(lat_d),
        "passenger_count": int(passengers),
    }


def compute_trip_signature(
    pickup_datetime: datetime,
    pickup_lon: float,
    pickup_lat: float,
    dropoff_lon: float,
    dropoff_lat: float,
    passenger_count: int,
) -> tuple:
    return (
        pickup_datetime.strftime("%Y-%m-%d %H:%M:%S"),
        round(float(pickup_lon), 3),
        round(float(pickup_lat), 3),
        round(float(dropoff_lon), 3),
        round(float(dropoff_lat), 3),
        int(passenger_count),
    )


def auto_estimate_fare(
    pickup_datetime: datetime,
    pickup_lon: float,
    pickup_lat: float,
    dropoff_lon: float,
    dropoff_lat: float,
    passenger_count: int,
) -> None:
    """Call /predict when trip inputs change; reuse cached result otherwise."""
    signature = compute_trip_signature(
        pickup_datetime, pickup_lon, pickup_lat, dropoff_lon, dropoff_lat, passenger_count
    )
    distance = haversine_km(pickup_lat, pickup_lon, dropoff_lat, dropoff_lon)

    if st.session_state.get("last_trip_signature") == signature:
        cached = st.session_state.get("cached_fare_result")
        if cached:
            render_fare(
                cached["fare"],
                cached["distance"],
                cached["passengers"],
                cached.get("latency_ms"),
            )
        return

    payload = trip_payload(
        pickup_datetime, pickup_lon, pickup_lat, dropoff_lon, dropoff_lat, passenger_count
    )

    with st.spinner("Calcul du tarif…"):
        try:
            t0 = time.perf_counter()
            fare_value = predict_one(payload)
            latency_ms = (time.perf_counter() - t0) * 1000
            st.session_state.last_trip_signature = signature
            st.session_state.cached_fare_result = {
                "fare": fare_value,
                "distance": distance,
                "passengers": passenger_count,
                "latency_ms": latency_ms,
            }
            render_fare(fare_value, distance, passenger_count, latency_ms)
        except requests.exceptions.Timeout:
            st.error("The prediction API timed out.")
        except requests.exceptions.RequestException as e:
            st.error(f"Unable to reach GET /predict: {e}")
        except (TypeError, ValueError) as e:
            st.error(str(e))


def render_fare(
    fare_value: float,
    distance: float,
    passengers: int,
    latency_ms: Optional[float] = None,
):
    note = "AI prediction · NYC US/Eastern time"
    if latency_ms is not None:
        note += f" · {latency_ms:.0f} ms"
    cpk = fare_value / max(distance, 0.01)

    st.markdown(
        f"""
        <div class="price-card">
            <div class="price-label">Estimated fare</div>
            <div class="price">${fare_value:.2f}</div>
            <div class="price-note">{note}</div>
            <div class="metric-row">
                <div class="metric">
                    <div class="metric-label">Distance</div>
                    <div class="metric-value">{distance:.2f} km</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Passengers</div>
                    <div class="metric-value">{passengers}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Cost / km</div>
                    <div class="metric-value">${cpk:.2f}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# HEADER
# ============================================================

current_theme = st.session_state.get("theme", DEFAULT_THEME)

head_left, head_right = st.columns([4, 1], gap="small", vertical_alignment="center")
with head_left:
    st.markdown(
        """
<div class="brand">
  <div class="brand-left">
    <div class="logo">🚕</div>
    <div>
      <div class="brand-name">TaxiFare</div>
      <div class="brand-tag">Fare Intelligence · optional API</div>
    </div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
with head_right:
    st.markdown('<div class="theme-toggle-anchor"></div>', unsafe_allow_html=True)
    st.button(
        THEME_LABELS.get(current_theme, "✨ Pro"),
        key="theme_toggle",
        type="secondary",
        on_click=cycle_theme,
        help="Pro → Nuit → Jour",
        use_container_width=True,
    )

st.markdown(
    APP_CSS + f"<style>{THEME_CSS.get(current_theme, PRO_THEME_CSS)}</style>",
    unsafe_allow_html=True,
)

# ============================================================
# SINGLE RIDE (GET /predict)
# ============================================================

if "preset_key" not in st.session_state:
    st.session_state.preset_key = "Times Square → JFK"
    for k, v in NYC_PRESETS[st.session_state.preset_key].items():
        st.session_state[k] = v
    st.session_state.map_fit_route = True
    pickup = place_by_filename("times_square.jpg")
    dropoff = place_by_filename("jfk_airport.jpg")
    if pickup:
        st.session_state.photo_pickup = pickup["filename"]
        set_address_field("pickup", pickup["label"])
    if dropoff:
        st.session_state.photo_dropoff = dropoff["filename"]
        set_address_field("dropoff", dropoff["label"])

consume_photo_click()
apply_pending_photo_points()
apply_pending_map_click()

render_photo_scenes()

left, mid, right = st.columns([0.95, 1.25, 0.95], gap="medium")

with left:
    st.markdown('<div class="kicker kicker-green">Départ</div>', unsafe_allow_html=True)
    render_address_search("pickup", "Rechercher une adresse…")

    st.markdown('<div class="kicker kicker-red">Arrivée</div>', unsafe_allow_html=True)
    render_address_search("dropoff", "Rechercher une adresse…")

    st.markdown(
        '<div class="kicker">Course</div><div class="trip-meta"></div>',
        unsafe_allow_html=True,
    )
    if isinstance(st.session_state.get("passenger_count"), float):
        st.session_state.passenger_count = int(st.session_state.passenger_count)
    ride_date = st.date_input(
        "Date",
        value=datetime.now().date(),
        format="DD/MM/YYYY",
    )
    time_col, pax_col = st.columns([1.45, 1], gap="small")
    with time_col:
        ride_time = st.time_input(
            "Heure",
            value=datetime.now().replace(second=0, microsecond=0).time(),
            step=60,
        )
    with pax_col:
        passenger_count = st.selectbox(
            "Passagers",
            options=[1, 2, 3, 4, 5, 6, 7, 8],
            key="passenger_count",
            format_func=lambda n: f"{n}",
        )

pickup_lat = float(st.session_state.pickup_latitude)
pickup_lon = float(st.session_state.pickup_longitude)
dropoff_lat = float(st.session_state.dropoff_latitude)
dropoff_lon = float(st.session_state.dropoff_longitude)

with mid:
    render_clickable_route_map(pickup_lat, pickup_lon, dropoff_lat, dropoff_lon)

with right:
    st.markdown(
        """
        <div class="section-head main-panel">
          <div class="section-title">Estimation</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    pickup_datetime = datetime.combine(ride_date, ride_time)
    auto_estimate_fare(
        pickup_datetime,
        pickup_lon,
        pickup_lat,
        dropoff_lon,
        dropoff_lat,
        passenger_count,
    )

# ============================================================
# FOOTER
# ============================================================

st.markdown(
    f"""
<div class="footer">
  TaxiFare <span>●</span> optional FastAPI
  &nbsp;·&nbsp; Built with Streamlit
</div>
""",
    unsafe_allow_html=True,
)
