import os
import streamlit as st
from helpers import DISPLAY_UNITS, TIME_UNITS

status_box = None


def render_sidebar():
    with st.sidebar:
        st.header("Controls")

        auto_refresh = st.toggle("Auto refresh", value=True)
        refresh_ms = st.slider("Refresh rate (ms)", 200, 5000, 800, step=100)
        max_points = st.slider("Keep last N points (in-memory)", 200, 50000, 10000, step=100)

        st.subheader("Time axis")
        time_unit = st.selectbox("Show time as", TIME_UNITS, index=0)
        window_seconds = st.slider("Visible time window (s)", 10, 600, 60, step=5)

        st.subheader("Smoothing")
        smooth_mode = st.selectbox("Method", ["None", "Rolling mean", "EMA (exponential)"], index=1)
        rolling_window = st.slider("Rolling window", 2, 200, 10)
        ema_alpha = st.slider("EMA alpha (higher = less smoothing)", 0.01, 0.99, 0.20)

        st.subheader("Display units")
        display_unit = st.selectbox("Show capacitance as", DISPLAY_UNITS, index=1)

        st.subheader("Plot display")
        plot_last_n = st.slider("Points to display", 200, 5000, 1000, step=100)
        chart_height = st.slider("Chart height", 350, 800, 575, step=25)

        st.subheader("Y axis")
        autoscale_y = st.toggle("Auto-scale Y", value=True)
        y_pad_pct = st.slider("Y padding (%)", 0, 50, 10)
        fixed_y = st.toggle("Use fixed Y range", value=False)
        y_min_manual = st.number_input("Y min", value=0.0)
        y_max_manual = st.number_input("Y max", value=20.0)

        show_raw = st.toggle("Show raw serial", value=True)
        raw_keep = st.slider("Raw lines to keep", 20, 1000, 200)

        st.divider()
        st.subheader("Channel collection")
        st.caption("If a channel is OFF, it will NOT be collected, logged, or plotted.")
        st.session_state["collect_C1"] = st.checkbox("Collect C1", value=st.session_state["collect_C1"])
        st.session_state["collect_C2"] = st.checkbox("Collect C2", value=st.session_state["collect_C2"])

        st.divider()
        st.subheader("Hours-long recording")
        st.caption("Enable logging so data is continuously written to CSV on disk.")
        log_enabled = st.toggle("Enable continuous logging to CSV", value=st.session_state["log_enabled"])
        log_folder_in = st.text_input(
            "Logging folder",
            value=st.session_state["log_folder"] or os.path.join(os.getcwd(), "arduino_logs"),
        )

        st.divider()
        st.caption("Arduino Serial Monitor must be CLOSED while this app connects to the COM port.")

        st.session_state["log_enabled"] = bool(log_enabled)
        st.session_state["log_folder"] = log_folder_in.strip()

    return {
        "auto_refresh": auto_refresh,
        "refresh_ms": refresh_ms,
        "max_points": max_points,
        "time_unit": time_unit,
        "smooth_mode": smooth_mode,
        "rolling_window": rolling_window,
        "ema_alpha": ema_alpha,
        "display_unit": display_unit,
        "autoscale_y": autoscale_y,
        "y_pad_pct": y_pad_pct,
        "show_raw": show_raw,
        "raw_keep": raw_keep,
        "window_seconds": window_seconds,
        "fixed_y": fixed_y,
        "y_min_manual": y_min_manual,
        "y_max_manual": y_max_manual,
        "plot_last_n": plot_last_n,
        "chart_height": chart_height,
    }


def render_connection_controls(ports):
    global status_box

    colA, colB, colC = st.columns([2, 2, 2], vertical_alignment="bottom")

    with colA:
        if ports:
            port = st.selectbox("Serial Port", ports, index=0)
        else:
            port = st.selectbox("Serial Port", ["No ports found"], index=0)
            port = None

    with colB:
        baud = st.selectbox("Baud Rate", [9600, 19200, 38400, 57600, 115200], index=4)

    with colC:
        st.session_state["paused"] = st.toggle("Pause", value=st.session_state["paused"])

    btn_col1, btn_col2, btn_col3, btn_col4 = st.columns([1, 1, 1, 2])

    with btn_col1:
        connect_clicked = st.button("Connect", use_container_width=True)

    with btn_col2:
        disconnect_clicked = st.button("Disconnect", use_container_width=True)

    with btn_col3:
        clear_clicked = st.button("Clear data (in-memory)", use_container_width=True)

    status_box = btn_col4.empty()

    return {
        "port": port,
        "baud": baud,
        "connect_clicked": connect_clicked,
        "disconnect_clicked": disconnect_clicked,
        "clear_clicked": clear_clicked,
    }


def set_status(msg: str, kind: str = "info"):
    global status_box

    if status_box is None:
        return

    if kind == "success":
        status_box.success(msg)
    elif kind == "error":
        status_box.error(msg)
    elif kind == "warning":
        status_box.warning(msg)
    else:
        status_box.info(msg)