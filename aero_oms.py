import random, time
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich import box
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="PNW Air Traffic Simulator")
    parser.add_argument("--ticks", type=int, default=30, help="Number of simulation steps")
    parser.add_argument("--flights", type=int, default=15, help="Number of concurrent flights")
    parser.add_argument("--realtime", type=float, default=0.8, help="Seconds per tick (e.g., 1 = real time)")
    return parser.parse_args()

PHASE_COLORS = {
    "Ground_Taxi": "white",
    "Takeoff": "green",
    "Initial_Climb": "bright_green",
    "Climb": "cyan",
    "Cruise": "blue",
    "Descent": "yellow",
    "Approach": "orange1",
    "Landing": "red",
    "GoAround": "magenta",
    "EmergencyDescent": "bold red"
}



# --- MOCK AIRPORT DATA ---
AIRPORTS = [
    {"icao": "KSEA", "lat": 47.4489, "lon": -122.3094},
    {"icao": "KPDX", "lat": 45.5887, "lon": -122.5975},
    {"icao": "KGEG", "lat": 47.619,  "lon": -117.533},
    {"icao": "KBOI", "lat": 43.5644, "lon": -116.2228},
    {"icao": "KPAE", "lat": 47.9063, "lon": -122.2816},
    {"icao": "KRNT", "lat": 47.4931, "lon": -122.215},
    {"icao": "KOLM", "lat": 46.9694, "lon": -122.903},
    {"icao": "KEUG", "lat": 44.1246, "lon": -123.2119},
    {"icao": "KBFI", "lat": 47.53,   "lon": -122.301},
    {"icao": "KTTD", "lat": 45.5494, "lon": -122.401}
]

PHASES = [
    "Ground_Taxi", "Takeoff", "Initial_Climb", "Climb", "Cruise",
    "Descent", "Approach", "Landing", "GoAround", "EmergencyDescent"
]

console = Console()

# --- CLASSES ---
class Airport:
    def __init__(self, icao, lat, lon):
        self.icao = icao
        self.lat = lat
        self.lon = lon

class Flight:
    def __init__(self, flight_id, origin, destination, departure_time):
        self.flight_id = flight_id
        self.origin = origin
        self.destination = destination
        self.departure_time = departure_time
        self.phase = "Ground_Taxi"
        self.altitude = 0
        self.ticks_in_phase = 0

    def step(self):
        phase_order = PHASES
        if self.phase in ["Landing", "EmergencyDescent"]:
            return
        i = phase_order.index(self.phase)
        if self.ticks_in_phase > random.randint(1, 3):
            self.phase = phase_order[i + 1] if i + 1 < len(phase_order) else self.phase
            self.ticks_in_phase = 0
        else:
            self.ticks_in_phase += 1
        self.altitude = self._simulate_altitude()

    def _simulate_altitude(self):
        phase_altitude = {
            "Ground_Taxi": 0,
            "Takeoff": 500,
            "Initial_Climb": 3000,
            "Climb": 12000,
            "Cruise": 35000,
            "Descent": 15000,
            "Approach": 3000,
            "Landing": 0,
            "GoAround": 2000,
            "EmergencyDescent": 1000
        }
        return phase_altitude.get(self.phase, 0)

# --- SETUP ---
def generate_flights(n=10):
    flights = []
    for i in range(n):
        origin, dest = random.sample(AIRPORTS, 2)
        flight_id = f"FL{i:03d}"
        flight = Flight(flight_id, origin["icao"], dest["icao"], departure_time=i)
        flights.append(flight)
    return flights

def render_table(flights, tick):
    table = Table(title=f"🛩️ PNW Air Traffic — Tick {tick}", box=box.SQUARE)
    table.add_column("Flight", style="bold cyan")
    table.add_column("From ➡ To", style="magenta")
    table.add_column("Phase", style="white")
    table.add_column("Altitude (ft)", justify="right")
    table.add_column("Status", style="white")

    for f in flights:
        phase_style = PHASE_COLORS.get(f.phase, "white")
        phase_text = f"[{phase_style}]{f.phase}[/{phase_style}]"

        status_icon = "✅" if f.phase not in ["GoAround", "EmergencyDescent"] else "⚠️"
        route = f"{f.origin} ➡ {f.destination}"
        table.add_row(f.flight_id, route, phase_text, str(f.altitude), status_icon)
    return table


# --- MAIN LOOP ---
def run_sim(duration_ticks, num_flights, tick_delay):
    flights = generate_flights(num_flights)
    with Live(render_table(flights, 0), refresh_per_second=2, console=console) as live:
        for tick in range(duration_ticks):
            for f in flights:
                f.step()
            live.update(render_table(flights, tick))
            time.sleep(tick_delay)

if __name__ == "__main__":
    args = parse_args()
    console.print("[bold blue]🛫 Starting Air Traffic CLI Simulator...")
    run_sim(args.ticks, args.flights, args.realtime)

