import random, time, csv
from datetime import datetime
from collections import deque
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich import box
import argparse
from geopy.distance import great_circle
from geopy import Point
import math

# --- PHASES & COLORS ---
PHASE_COLORS = {
    "Ground_Taxi": "white",
    "Queued": "grey50",
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

PHASES = [
    "Ground_Taxi", "Queued", "Takeoff", "Initial_Climb", "Climb", "Cruise",
    "Descent", "Approach", "Landing", "GoAround", "EmergencyDescent"
]

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

console = Console()

# --- GEODESY UTILS ---
def calculate_bearing(start_lat, start_lon, end_lat, end_lon):
    # Returns initial bearing in degrees from start to end
    start = Point(start_lat, start_lon)
    end = Point(end_lat, end_lon)
    lat1 = math.radians(start.latitude)
    lat2 = math.radians(end.latitude)
    diff_long = math.radians(end.longitude - start.longitude)
    x = math.sin(diff_long) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1) * math.cos(lat2) * math.cos(diff_long))
    initial_bearing = math.atan2(x, y)
    initial_bearing = math.degrees(initial_bearing)
    compass_bearing = (initial_bearing + 360) % 360
    return compass_bearing

def move_point(lat, lon, bearing, distance_nm):
    # Move a point by a bearing and distance (in nautical miles)
    origin = Point(lat, lon)
    destination = great_circle(nautical=distance_nm).destination(origin, bearing)
    return destination.latitude, destination.longitude

# --- CLASSES ---
class Airport:
    def __init__(self, icao, lat, lon):
        self.icao = icao
        self.lat = lat
        self.lon = lon
        self.runway_queue = deque()
        self.runway_busy_until = 0
        self.utilization = 0

class Flight:
    # Realistic speeds (knots)
    PHASE_SPEEDS = {
        "Ground_Taxi": 15,
        "Queued": 0,
        "Takeoff": 140,
        "Initial_Climb": 220,
        "Climb": 350,
        "Cruise": 450,
        "Descent": 350,
        "Approach": 180,
        "Landing": 0,
        "GoAround": 200,
        "EmergencyDescent": 250
    }
    def __init__(self, flight_id, origin, destination, departure_time, origin_lat, origin_lon, dest_lat, dest_lon):
        self.flight_id = flight_id
        self.origin = origin
        self.destination = destination
        self.departure_time = departure_time
        self.phase = "Ground_Taxi"
        self.altitude = 0
        self.ticks_in_phase = 0
        self.delay = 0
        self.queued = False
        self.takeoff_clearance = False
        self.lat = origin_lat
        self.lon = origin_lon
        self.dest_lat = dest_lat
        self.dest_lon = dest_lon
        self.route_distance_nm = great_circle((origin_lat, origin_lon), (dest_lat, dest_lon)).nautical
        self.distance_travelled_nm = 0
        self.bearing = calculate_bearing(origin_lat, origin_lon, dest_lat, dest_lon)

    def step(self, tick, airport, controller, tick_minutes=1):
        # If not yet queued for takeoff, join the queue
        if self.phase == "Ground_Taxi" and not self.queued:
            airport.runway_queue.append(self)
            self.phase = "Queued"
            self.queued = True
            return
        # If queued, wait for controller clearance
        if self.phase == "Queued":
            if controller.approve_takeoff(self, airport, tick):
                self.phase = "Takeoff"
                self.ticks_in_phase = 0
                self.takeoff_clearance = True
                airport.runway_busy_until = tick + controller.spacing_buffer
                airport.utilization += 1
            else:
                self.delay += 1
            return
        # Move the flight if airborne
        if self.phase in ["Takeoff", "Initial_Climb", "Climb", "Cruise", "Descent", "Approach"]:
            speed = self.PHASE_SPEEDS[self.phase]  # knots
            distance_this_tick = (speed * tick_minutes) / 60  # nautical miles per tick
            self.distance_travelled_nm += distance_this_tick
            # Move position along bearing
            self.lat, self.lon = move_point(self.lat, self.lon, self.bearing, distance_this_tick)
        # Phase progression based on distance
        self._update_phase()
        self.altitude = self._simulate_altitude()
        self.ticks_in_phase += 1

    def _update_phase(self):
        # Example: simple logic for phase transitions based on distance
        if self.phase == "Takeoff" and self.distance_travelled_nm > 2:
            self.phase = "Initial_Climb"
            self.ticks_in_phase = 0
        elif self.phase == "Initial_Climb" and self.distance_travelled_nm > 10:
            self.phase = "Climb"
            self.ticks_in_phase = 0
        elif self.phase == "Climb" and self.distance_travelled_nm > 40:
            self.phase = "Cruise"
            self.ticks_in_phase = 0
        elif self.phase == "Cruise" and self.distance_travelled_nm > self.route_distance_nm - 40:
            self.phase = "Descent"
            self.ticks_in_phase = 0
        elif self.phase == "Descent" and self.distance_travelled_nm > self.route_distance_nm - 10:
            self.phase = "Approach"
            self.ticks_in_phase = 0
        elif self.phase == "Approach" and self.distance_travelled_nm >= self.route_distance_nm:
            self.phase = "Landing"
            self.ticks_in_phase = 0

    def _simulate_altitude(self):
        phase_altitude = {
            "Ground_Taxi": 0,
            "Queued": 0,
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

class ControllerAI:
    def __init__(self, spacing_buffer=2):
        self.spacing_buffer = spacing_buffer
    def approve_takeoff(self, flight, airport, tick):
        return tick >= airport.runway_busy_until and airport.runway_queue and airport.runway_queue[0] == flight

# --- SETUP ---
def generate_flights(n=10):
    flights = []
    for i in range(n):
        origin, dest = random.sample(AIRPORTS, 2)
        flight_id = f"FL{i:03d}"
        flight = Flight(
            flight_id,
            origin["icao"], dest["icao"],
            departure_time=i,
            origin_lat=origin["lat"], origin_lon=origin["lon"],
            dest_lat=dest["lat"], dest_lon=dest["lon"]
        )
        flights.append(flight)
    return flights

def render_table(flights, tick):
    table = Table(title=f"🛩️ Regional Air Traffic v3 — Tick {tick}", box=box.SQUARE)
    table.add_column("Flight", style="bold cyan")
    table.add_column("From ➡ To", style="magenta")
    table.add_column("Phase", style="white")
    table.add_column("Lat", justify="right")
    table.add_column("Lon", justify="right")
    table.add_column("Dist (nm)", justify="right")
    table.add_column("Delay", justify="right")
    table.add_column("Status", style="white")
    for f in flights:
        phase_style = PHASE_COLORS.get(f.phase, "white")
        phase_text = f"[{phase_style}]{f.phase}[/{phase_style}]"
        status_icon = "✅" if f.phase not in ["GoAround", "EmergencyDescent"] else "⚠️"
        route = f"{f.origin} ➡ {f.destination}"
        table.add_row(
            f.flight_id, route, phase_text,
            f"{f.lat:.3f}", f"{f.lon:.3f}",
            f"{f.distance_travelled_nm:.1f}/{f.route_distance_nm:.1f}",
            str(f.delay), status_icon
        )
    return table

def log_to_csv(flights, tick, filename="sim_log.csv"):
    fieldnames = ["tick", "flight_id", "origin", "destination", "phase", "lat", "lon", "distance_travelled_nm", "route_distance_nm", "altitude", "delay"]
    write_header = tick == 0
    with open(filename, "a", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        for f in flights:
            writer.writerow({
                "tick": tick,
                "flight_id": f.flight_id,
                "origin": f.origin,
                "destination": f.destination,
                "phase": f.phase,
                "lat": f.lat,
                "lon": f.lon,
                "distance_travelled_nm": f.distance_travelled_nm,
                "route_distance_nm": f.route_distance_nm,
                "altitude": f.altitude,
                "delay": f.delay
            })

# --- MAIN LOOP ---
def run_sim(duration_ticks, num_flights, tick_delay, tick_minutes=1):
    airports = {a["icao"]: Airport(a["icao"], a["lat"], a["lon"]) for a in AIRPORTS}
    flights = generate_flights(num_flights)
    controller = ControllerAI(spacing_buffer=2)
    with Live(render_table(flights, 0), refresh_per_second=2, console=console) as live:
        for tick in range(duration_ticks):
            for f in flights:
                airport = airports[f.origin]
                f.step(tick, airport, controller, tick_minutes=tick_minutes)
                if f.phase == "Takeoff" and airport.runway_queue and airport.runway_queue[0] == f:
                    airport.runway_queue.popleft()
            live.update(render_table(flights, tick))
            log_to_csv(flights, tick)
            time.sleep(tick_delay)
    for icao, ap in airports.items():
        console.print(f"[bold green]{icao} runway utilization: {ap.utilization} takeoffs")

def parse_args():
    parser = argparse.ArgumentParser(description="Regional Air Traffic Simulator v3 (with geodesy)")
    parser.add_argument("--ticks", type=int, default=10000, help="Number of simulation steps")
    parser.add_argument("--flights", type=int, default=30, help="Number of concurrent flights")
    parser.add_argument("--realtime", type=float, default=0.05, help="Seconds per tick (simulation speed)")
    parser.add_argument("--tick_minutes", type=float, default=1, help="Simulated minutes per tick")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    console.print("[bold blue]🛫 Starting Regional Air Traffic CLI Simulator v3 (geodesy)...")
    run_sim(args.ticks, args.flights, args.realtime, tick_minutes=args.tick_minutes)

# ---
# Requirements:
#   pip install rich geopy
# --- 