# Dinner Survey App

A premium-styled web application for surveying team dinner dates.
Built with **Streamlit** and **Python**.

## Features
- **Interactive Calendar**: Select dates directly from a monthly grid.
- **List View**: Alternative selection via a scrollable list.
- **Two-way Sync**: Calendar and List always stay in sync.
- **Selection Limit**: Enforces a maximum of 3 selected dates.
- **Premium Design**: Modern aesthetics with glassmorphism and micro-animations.

## How to Run

This project is designed to run in the `work` Conda environment.

1. **Activate the environment** (if not already active):
   ```bash
   conda activate work
   ```

2. **Run the application**:
   ```bash
   streamlit run script/app.py
   ```

3. **Open in Browser**:
   The terminal will show a URL (usually http://localhost:8501). Click it to use the app.

## Project Structure
- `script/`: Contains the source code (`app.py`, `components.py`, `styles.css`).
- `output/`: Directory for any generated data.
- `data/`: Directory for input data.
