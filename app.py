import base64
import math
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import folium
import requests
import streamlit as st
from dotenv import load_dotenv
from streamlit_folium import st_folium

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
ROOT_URL = f"{API_BASE}/"

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
]

# ============================================================
# CSS — keep TaxiFare yellow night identity, add motion
# ============================================================

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');

:root {
    --bg: #07090d;
    --border: rgba(255,255,255,0.08);
    --text: #f5f7fa;
    --muted: #8d96a5;
    --yellow: #f7c948;
    --green: #47e6a1;
    --red: #ff6b7a;
}

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

.stApp {
    background:
        radial-gradient(circle at 12% 8%, rgba(247,201,72,0.10), transparent 32%),
        radial-gradient(circle at 88% 12%, rgba(71,230,161,0.06), transparent 30%),
        radial-gradient(circle at 50% 100%, rgba(247,201,72,0.04), transparent 40%),
        var(--bg);
    color: var(--text);
}

.block-container {
    max-width: 1280px;
    padding-top: 0.7rem;
    padding-bottom: 0.8rem;
}

#MainMenu, footer, header, [data-testid="stHeader"] { display: none !important; }

[data-testid="stVerticalBlock"] { gap: 0.45rem !important; }
[data-testid="stWidgetLabel"] { margin-bottom: 0.1rem; }
[data-testid="stWidgetLabel"] p { font-size: 12px !important; font-weight: 600; }
[data-testid="InputInstructions"] { display: none !important; }
[data-testid="stCaptionContainer"] { margin-top: 0.15rem !important; }

@keyframes pulse-dot {
    0%, 100% { box-shadow: 0 0 0 0 rgba(71,230,161,0.7); }
    50% { box-shadow: 0 0 0 8px rgba(71,230,161,0); }
}
@keyframes fare-in {
    from { opacity: 0; transform: translateY(12px) scale(0.98); }
    to { opacity: 1; transform: translateY(0) scale(1); }
}
@keyframes glow-route {
    0%, 100% { filter: drop-shadow(0 0 4px rgba(247,201,72,0.35)); }
    50% { filter: drop-shadow(0 0 14px rgba(247,201,72,0.7)); }
}

.brand {
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 0.55rem;
}
.brand-left { display: flex; align-items: center; gap: 12px; }
.logo {
    width: 36px; height: 36px; border-radius: 11px;
    background: linear-gradient(135deg, #f7c948, #ffdf78);
    display: flex; align-items: center; justify-content: center;
    color: #0a0b0e; font-size: 18px;
    box-shadow: 0 8px 24px rgba(247,201,72,0.25);
    animation: glow-route 3.2s ease-in-out infinite;
}
.brand-name {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 18px; font-weight: 700; letter-spacing: -0.4px;
}
.brand-tag { color: var(--muted); font-size: 11px; }

.status {
    display: flex; align-items: center; gap: 8px;
    color: #aab3c0; font-size: 11px;
    background: rgba(255,255,255,0.035);
    border: 1px solid var(--border);
    padding: 6px 11px; border-radius: 999px;
}
.status.offline { color: #c9a0a5; }
.status-dot {
    width: 7px; height: 7px; border-radius: 50%;
    background: var(--green);
    animation: pulse-dot 1.8s ease-in-out infinite;
}
.status.offline .status-dot {
    background: var(--red);
    animation: none;
    box-shadow: none;
}

.panel {
    background: linear-gradient(145deg, rgba(255,255,255,0.045), rgba(255,255,255,0.015));
    border: 1px solid var(--border);
    border-radius: 22px;
    padding: 22px 24px 8px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.22), inset 0 1px 0 rgba(255,255,255,0.03);
    margin-bottom: 1rem;
}
.panel-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 17px; font-weight: 600; margin-bottom: 2px;
}
.panel-sub { color: var(--muted); font-size: 13px; margin-bottom: 14px; }

.price-card {
    margin-top: 0; padding: 20px 18px 16px; border-radius: 18px;
    text-align: center;
    background:
        radial-gradient(circle at 80% 10%, rgba(247,201,72,0.14), transparent 42%),
        rgba(247,201,72,0.04);
    border: 1px solid rgba(247,201,72,0.18);
    animation: fare-in 0.55s cubic-bezier(.2,.8,.2,1);
}
.price-label {
    color: var(--muted); font-size: 13px; text-transform: uppercase;
    letter-spacing: 1.8px; font-weight: 700;
}
.price {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 56px; line-height: 1; letter-spacing: -2px;
    font-weight: 700; color: var(--yellow); margin-top: 10px;
}
.price-note { color: #707987; font-size: 13px; margin-top: 8px; }

.metric-row {
    display: grid; grid-template-columns: 1fr; gap: 8px; margin-top: 16px;
}
.metric {
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px; padding: 12px 10px;
    text-align: center;
}
.metric-label {
    color: #707987; font-size: 11px; text-transform: uppercase; letter-spacing: 1.2px;
}
.metric-value {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 22px; font-weight: 600; margin-top: 4px;
}

.stButton > button {
    width: 100%; border: none; border-radius: 10px; min-height: 38px;
    background: linear-gradient(135deg, #f7c948, #ffdc73);
    color: #0a0b0e;
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700; font-size: 13px;
    transition: all 0.2s ease;
    box-shadow: 0 8px 22px rgba(247,201,72,0.14);
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 16px 45px rgba(247,201,72,0.28);
}
.stButton > button[kind="secondary"],
.stButton > button[data-testid="baseButton-secondary"] {
    background: rgba(255,255,255,0.06);
    color: var(--text);
    box-shadow: none;
    border: 1px solid rgba(255,255,255,0.09);
}
.stButton > button[kind="secondary"]:hover,
.stButton > button[data-testid="baseButton-secondary"]:hover {
    background: rgba(255,255,255,0.10);
    box-shadow: none;
}

div[data-baseweb="input"] > div,
div[data-baseweb="select"] > div,
div[data-baseweb="base-input"] {
    background: #0a0e14 !important;
    border: 1px solid rgba(255,255,255,0.09) !important;
    border-radius: 12px !important;
}
input { color: white !important; }

div[data-testid="stHorizontalBlock"]:has(.scene-card) {
    gap: 0.55rem !important;
}
div[data-testid="stHorizontalBlock"]:has(.scene-card) [data-testid="stVerticalBlock"] {
    gap: 0.28rem !important;
}
div[data-testid="stHorizontalBlock"]:has(.scene-card) .stButton > button {
    min-height: 30px;
    font-size: 12px;
    border-radius: 8px;
    box-shadow: none;
}

.scene-card {
    border-radius: 12px;
    overflow: hidden;
    line-height: 0;
    border: 3px solid transparent;
    background: rgba(255,255,255,0.03);
}
.scene-card img {
    width: 100%;
    height: 56px;
    object-fit: cover;
    display: block;
}
.scene-card.pickup {
    border-color: var(--green);
    box-shadow: 0 0 12px rgba(71,230,161,0.35);
}
.scene-card.dropoff {
    border-color: var(--red);
    box-shadow: 0 0 12px rgba(255,107,122,0.35);
}

.footer {
    text-align: center; margin-top: 10px; color: #4f5866; font-size: 10px;
}
.footer span { color: var(--yellow); }

iframe { border-radius: 14px; }
</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# HELPERS
# ============================================================

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
    st.session_state.map_click_target = None


def on_preset_change() -> None:
    load_preset(st.session_state.preset_key)


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
    if "dropoff" in pending:
        place = pending["dropoff"]
        st.session_state.dropoff_latitude = place["latitude"]
        st.session_state.dropoff_longitude = place["longitude"]
    st.session_state.map_click_target = None

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
    """Apply a map click queued on the previous run, before coordinate widgets mount."""
    pending = st.session_state.pop("pending_map_click", None)
    if not pending:
        return

    lat, lon = pending["lat"], pending["lon"]
    if pending["target"] == "pickup":
        st.session_state.pickup_latitude = lat
        st.session_state.pickup_longitude = lon
        st.session_state.photo_pickup = None
    else:
        st.session_state.dropoff_latitude = lat
        st.session_state.dropoff_longitude = lon
        st.session_state.photo_dropoff = None


def render_clickable_route_map(
    pickup_lat: float,
    pickup_lon: float,
    dropoff_lat: float,
    dropoff_lon: float,
) -> None:
    """Place pickup/dropoff by first choosing a button, then clicking the map."""
    if "map_click_target" not in st.session_state:
        st.session_state.map_click_target = None
    if "last_map_click" not in st.session_state:
        st.session_state.last_map_click = None

    target = st.session_state.map_click_target

    b1, b2 = st.columns(2)
    with b1:
        pickup_clicked = st.button(
            "Départ",
            key="add_pickup_point",
            type="primary" if target == "pickup" else "secondary",
            use_container_width=True,
        )
    with b2:
        dropoff_clicked = st.button(
            "Arrivée",
            key="add_dropoff_point",
            type="primary" if target == "dropoff" else "secondary",
            use_container_width=True,
        )

    if pickup_clicked:
        st.session_state.map_click_target = None if target == "pickup" else "pickup"
        st.rerun()
    if dropoff_clicked:
        st.session_state.map_click_target = None if target == "dropoff" else "dropoff"
        st.rerun()

    if target == "pickup":
        st.caption("Cliquez la carte pour le **départ**")
    elif target == "dropoff":
        st.caption("Cliquez la carte pour l'**arrivée**")

    center_lat = (pickup_lat + dropoff_lat) / 2
    center_lon = (pickup_lon + dropoff_lon) / 2

    route_map = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=11,
        tiles="CartoDB positron",
    )

    folium.Marker(
        [pickup_lat, pickup_lon],
        tooltip="Départ",
        popup=f"Départ<br>{pickup_lat:.5f}, {pickup_lon:.5f}",
        icon=folium.Icon(color="green", icon="info-sign"),
    ).add_to(route_map)

    folium.Marker(
        [dropoff_lat, dropoff_lon],
        tooltip="Arrivée",
        popup=f"Arrivée<br>{dropoff_lat:.5f}, {dropoff_lon:.5f}",
        icon=folium.Icon(color="red", icon="info-sign"),
    ).add_to(route_map)

    folium.PolyLine(
        [[pickup_lat, pickup_lon], [dropoff_lat, dropoff_lon]],
        color="#f7c948",
        weight=4,
        opacity=0.85,
    ).add_to(route_map)

    map_data = st_folium(
        route_map,
        width=None,
        height=300,
        returned_objects=["last_clicked"],
        key="route_map_clicker",
    )

    clicked = (map_data or {}).get("last_clicked")
    if not clicked:
        return

    click_key = (round(clicked["lat"], 3), round(clicked["lng"], 3))
    if click_key == st.session_state.get("last_map_click"):
        return

    st.session_state.last_map_click = click_key
    if not target:
        return

    lat, lon = click_key
    st.session_state.pending_map_click = {"target": target, "lat": lat, "lon": lon}
    st.session_state.map_click_target = None
    st.rerun()


@st.cache_data
def place_image_uri(filename: str) -> str:
    data = (ASSETS_DIR / filename).read_bytes()
    return f"data:image/jpeg;base64,{base64.b64encode(data).decode()}"


def render_photo_scenes() -> None:
    """Photos are places: first click sets pickup, second sets dropoff."""
    if "photo_pickup" not in st.session_state:
        st.session_state.photo_pickup = None
        st.session_state.photo_dropoff = None

    for row_start in range(0, len(DEMO_IMAGES), 4):
        demo_cols = st.columns(4, gap="small")
        for i, demo in enumerate(DEMO_IMAGES[row_start : row_start + 4]):
            idx = row_start + i
            is_pickup = st.session_state.photo_pickup == demo["filename"]
            is_dropoff = st.session_state.photo_dropoff == demo["filename"]
            if is_pickup:
                frame = "pickup"
                label = f"Départ · {demo['label']}"
            elif is_dropoff:
                frame = "dropoff"
                label = f"Arrivée · {demo['label']}"
            else:
                frame = ""
                label = demo["label"]

            with demo_cols[i]:
                st.markdown(
                    f'<div class="scene-card {frame}">'
                    f'<img src="{place_image_uri(demo["filename"])}" alt="{demo["label"]}">'
                    f"</div>",
                    unsafe_allow_html=True,
                )
                if st.button(
                    label,
                    key=f"demo_img_{idx}",
                    type="secondary",
                ):
                    queue_photo_point(demo)
                    st.rerun()


@st.cache_data(ttl=30)
def api_is_up(root_url: str) -> bool:
    try:
        r = requests.get(root_url, timeout=4)
        return r.status_code == 200
    except requests.RequestException:
        return False


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

online = api_is_up(ROOT_URL)
status_class = "status" if online else "status offline"
status_label = "API online" if online else "API offline"

st.markdown(
    f"""
<div class="brand">
  <div class="brand-left">
    <div class="logo">🚕</div>
    <div>
      <div class="brand-name">TaxiFare</div>
      <div class="brand-tag">Fare Intelligence · optional API</div>
    </div>
  </div>
  <div class="{status_class}">
    <div class="status-dot"></div>
    {status_label}
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# ============================================================
# SINGLE RIDE (GET /predict)
# ============================================================

if "preset_key" not in st.session_state:
    st.session_state.preset_key = "Times Square → JFK"
    for k, v in NYC_PRESETS[st.session_state.preset_key].items():
        st.session_state[k] = v

apply_pending_photo_points()
apply_pending_map_click()

render_photo_scenes()

left, mid, right = st.columns([0.9, 1.2, 0.85], gap="medium")

with left:
    st.selectbox(
        "Trajet NYC",
        list(NYC_PRESETS.keys()),
        key="preset_key",
        on_change=on_preset_change,
    )

    c1, c2 = st.columns(2)
    with c1:
        pickup_lat = st.number_input(
            "Pickup lat", format="%.3f", step=0.001, key="pickup_latitude"
        )
    with c2:
        pickup_lon = st.number_input(
            "Pickup lon", format="%.3f", step=0.001, key="pickup_longitude"
        )

    c1, c2 = st.columns(2)
    with c1:
        dropoff_lat = st.number_input(
            "Dropoff lat", format="%.3f", step=0.001, key="dropoff_latitude"
        )
    with c2:
        dropoff_lon = st.number_input(
            "Dropoff lon", format="%.3f", step=0.001, key="dropoff_longitude"
        )

    c1, c2, c3 = st.columns(3)
    with c1:
        ride_date = st.date_input("Date", value=datetime.now().date())
    with c2:
        ride_time = st.time_input(
            "Heure",
            value=datetime.now().replace(second=0, microsecond=0).time(),
        )
    with c3:
        passenger_count = st.number_input(
            "Passagers",
            min_value=1,
            max_value=8,
            step=1,
            key="passenger_count",
        )

with mid:
    render_clickable_route_map(pickup_lat, pickup_lon, dropoff_lat, dropoff_lon)

with right:
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
