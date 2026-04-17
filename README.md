# Arduino Live Capacitance Grapher

A real-time data visualization tool for Arduino-based capacitance measurements. This app reads serial data from an Arduino, parses capacitance values, and displays them live using an interactive Streamlit dashboard.

Features:
- Live plotting of capacitance vs time (C1, C2 channels)
- Serial communication with Arduino (pyserial)
- Data smoothing (rolling mean / EMA)
- Adjustable units (pF → F) and time scales
- Continuous CSV logging for long experiments
- Export plots and data

The app is built using Python, Streamlit, and Plotly for smooth and interactive visualization.

Python Dependencies (IMPORTANT)
pip install streamlit pandas numpy plotly pyserial
