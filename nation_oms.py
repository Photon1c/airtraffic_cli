import random
import time
from rich.console import Console
from rich.table import Table
from rich import box
from rich.live import Live
from rich.layout import Layout

# --- FAA REGIONS & FLIGHT TYPE DATA (from airtraffic.md) ---
FAA_REGIONS = [
    {"name": "Alaskan", "code": "AL", "flights": {"🛫": 300, "🛩️": 1500, "🚕": 500, "🪖": 150, "📦": 50}},
    {"name": "Central", "code": "CE", "flights": {"🛫": 2100, "🛩️": 2800, "🚕": 1400, "🪖": 600, "📦": 300}},
    {"name": "Eastern", "code": "EA", "flights": {"🛫": 4800, "🛩️": 3600, "🚕": 2000, "🪖": 400, "📦": 600}},
    {"name": "Great Lakes", "code": "GL", "flights": {"🛫": 3600, "🛩️": 4500, "🚕": 1800, "🪖": 400, "📦": 500}},
    {"name": "New England", "code": "NE", "flights": {"🛫": 1800, "🛩️": 1200, "🚕": 600, "🪖": 100, "📦": 200}},
    {"name": "Northwest Mtn.", "code": "NM", "flights": {"🛫": 2900, "🛩️": 3000, "🚕": 1500, "🪖": 300, "📦": 400}},
    {"name": "Southern", "code": "SO", "flights": {"🛫": 5100, "🛩️": 4900, "🚕": 2300, "🪖": 600, "📦": 800}},
    {"name": "Southwest", "code": "SW", "flights": {"🛫": 3400, "🛩️": 3200, "🚕": 1900, "🪖": 700, "📦": 700}},
    {"name": "Western-Pacific", "code": "WP", "flights": {"🛫": 3000, "🛩️": 2500, "🚕": 1500, "🪖": 1000, "📦": 600}},
    {"name": "Headquarters (DC)", "code": "HQ", "flights": {"🛫": 500, "🛩️": 200, "🚕": 100, "🪖": 100, "📦": 100}},
    {"name": "GUAM/HI (Pacific)", "code": "PI", "flights": {"🛫": 400, "🛩️": 600, "🚕": 200, "🪖": 200, "📦": 100}},
]

FLIGHT_TYPE_EMOJIS = ["🛫", "🛩️", "🚕", "🪖", "📦"]
FLIGHT_TYPE_NAMES = ["Commercial", "General Aviation", "Air Taxi", "Military", "Cargo"]

console = Console()

class Flight:
    def __init__(self, region_code, flight_type, flight_id, duration):
        self.region_code = region_code
        self.flight_type = flight_type  # Emoji
        self.flight_id = flight_id
        self.status = "Scheduled"  # Scheduled, Enroute, Landed
        self.progress = 0  # Minutes flown
        self.duration = duration  # Total minutes for flight
        self.start_time = None  # Tick when flight starts
        self.end_time = None  # Tick when flight lands

    def step(self, tick):
        if self.status == "Scheduled" and tick >= self.start_time:
            self.status = "Enroute"
        if self.status == "Enroute":
            self.progress += 1
            if self.progress >= self.duration:
                self.status = "Landed"
                self.end_time = tick

# Generate all flights for all regions
def generate_flights(seed=42):
    random.seed(seed)
    flights = []
    for region in FAA_REGIONS:
        for emoji in FLIGHT_TYPE_EMOJIS:
            n = region["flights"].get(emoji, 0)
            for i in range(n):
                flight_id = f"{region['code']}-{emoji}-{i+1:04d}"
                # Randomly assign a start time within the first 6 hours (360 min)
                start_time = random.randint(0, 360)
                # Assign a duration based on type (in minutes)
                if emoji == "🛫":
                    duration = random.randint(60, 240)  # Commercial
                elif emoji == "🛩️":
                    duration = random.randint(30, 120)  # GA
                elif emoji == "🚕":
                    duration = random.randint(20, 90)   # Air Taxi
                elif emoji == "🪖":
                    duration = random.randint(40, 180)  # Military
                elif emoji == "📦":
                    duration = random.randint(60, 180)  # Cargo
                f = Flight(region['code'], emoji, flight_id, duration)
                f.start_time = start_time
                flights.append(f)
    return flights

def summarize_by_region(flights):
    # Count flights by region, type, and status
    summary = {region["code"]: {emoji: {"Enroute": 0, "Landed": 0, "Scheduled": 0} for emoji in FLIGHT_TYPE_EMOJIS} for region in FAA_REGIONS}
    for f in flights:
        summary[f.region_code][f.flight_type][f.status] += 1
    return summary

def make_summary_table(summary):
    table = Table(title="🗺️ U.S. National Airspace Simulation — FAA Regions", box=box.SQUARE)
    table.add_column("Region", style="bold cyan")
    for emoji, name in zip(FLIGHT_TYPE_EMOJIS, FLIGHT_TYPE_NAMES):
        table.add_column(f"{emoji}\nEnroute", justify="right")
        table.add_column(f"{emoji}\nLanded", justify="right")
    table.add_column("Total Enroute", style="bold yellow", justify="right")
    table.add_column("Total Landed", style="bold yellow", justify="right")
    for region in FAA_REGIONS:
        code = region["code"]
        row = [region["name"]]
        total_enroute = 0
        total_landed = 0
        for emoji in FLIGHT_TYPE_EMOJIS:
            enroute = summary[code][emoji]["Enroute"]
            landed = summary[code][emoji]["Landed"]
            row.append(str(enroute))
            row.append(str(landed))
            total_enroute += enroute
            total_landed += landed
        row.append(str(total_enroute))
        row.append(str(total_landed))
        table.add_row(*row)
    return table

def make_flight_sample_table(flights, tick, sample_size=20):
    # Show a sample of active flights
    active = [f for f in flights if f.status == "Enroute"]
    sample = random.sample(active, min(sample_size, len(active))) if active else []
    table = Table(title=f"✈️ Sample of Active Flights (Tick {tick})", box=box.SQUARE)
    table.add_column("Flight ID", style="bold cyan")
    table.add_column("Region", style="magenta")
    table.add_column("Type", style="white")
    table.add_column("Progress", justify="right")
    table.add_column("Duration", justify="right")
    table.add_column("Status", style="green")
    for f in sample:
        pct = int(100 * f.progress / f.duration) if f.duration else 0
        table.add_row(f.flight_id, f.region_code, f.flight_type, f"{f.progress}/{f.duration} min ({pct}%)", str(f.duration), f.status)
    return table

def run_sim(ticks=10000, realtime=1.0):
    flights = generate_flights()
    with Live(console=console, refresh_per_second=2) as live:
        for tick in range(ticks):
            for f in flights:
                f.step(tick)
            summary = summarize_by_region(flights)
            summary_table = make_summary_table(summary)
            sample_table = make_flight_sample_table(flights, tick)
            grid = Table.grid()
            grid.add_row(summary_table)
            grid.add_row(sample_table)
            live.update(grid)
            time.sleep(realtime)

if __name__ == "__main__":
    run_sim(ticks=10000, realtime=1.0)

# ---
# This script now simulates live, minute-by-minute flight progress for the entire U.S. airspace.
# The dashboard updates in real time and can be left running in the background.
# --- 