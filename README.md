# Regional Air Traffic Control Simulator

A lightweight, modular air traffic simulation tool for prototyping, education, and research. Simulates flights between Pacific Northwest airports, with runway queueing, controller AI, and data logging.

## Features
- Simulates multiple flights between real PNW airports
- Runway slotting and takeoff queue logic
- Simple controller AI for sequencing and spacing
- Tracks delays, runway utilization, and go-arounds
- Logs simulation data to CSV for analysis
- Rich CLI visualization with color-coded flight phases

## Usage

### Requirements
- Python 3.7+
- `rich` library (`pip install rich`)

### Running the Simulator

#### Version 1 (Basic):
```bash
python aero_oms.py --ticks 30 --flights 15 --realtime 0.8
```

#### Version 2 (With Runway Queue, AI, Logging):
```bash
python aeri_oms_v2.py --ticks 30 --flights 15 --realtime 0.8
```
- `--ticks`: Number of simulation steps
- `--flights`: Number of concurrent flights
- `--realtime`: Seconds per tick (simulation speed)

### Output
- CLI table showing all flights, their phases, altitudes, and delays
- At simulation end, runway utilization per airport is printed
- `sim_log.csv`: Detailed log of all flights at each tick

## File Descriptions
- `aero_oms.py`: Original simulator. Simulates basic flight phases with CLI visualization.
- `aeri_oms_v2.py`: Enhanced simulator with runway queue, controller AI, delay tracking, and CSV logging. Modular for future upgrades.
- `development/feedback.log`: AI and user feedback, feature ideas, and roadmap notes.
- `development/progress.log`: Milestone and progress tracking (see for latest changes).
- `development/progresstemplate.md`: Template for progress logs.

## Next Steps / Roadmap
- Add weather diversions, emergencies, and go-arounds
- Implement conflict detection and deconfliction AI
- Add interactive ATC trainer mode or human-in-the-loop CLI prompts
- Visualize airspace and traffic density with Plotly or Dash

## License
MIT (or specify your own) 
