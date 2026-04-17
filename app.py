import time
import pandas as pd
import streamlit as st

from parsing import parse_cap_line
from serial_reader import SerialConfig, SerialReader, get_available_ports, serial
from helpers import (
    DATA_COLUMNS,
    ensure_run_folder,
    init_logfile,
    append_rows_to_csv,
)
from state import init_state
from ui_components import render_sidebar, render_connection_controls, set_status
from plotter import (
    render_plot_section,
    render_latest_values_section,
    render_save_section,
    render_raw_serial,
)

st.set_page_config(page_title="Arduino Live Grapher", layout="wide")


def handle_connection_actions(connect_clicked, disconnect_clicked, clear_clicked, port, baud):
    if connect_clicked:
        st.session_state["last_error"] = ""

        if st.session_state["reader"] is not None:
            try:
                st.session_state["reader"].stop()
            except Exception:
                pass
            st.session_state["reader"] = None

        st.session_state["t0_time_s"] = None

        if not serial:
            st.session_state["connected"] = False
            st.session_state["last_error"] = "pyserial not available. Install with: python -m pip install pyserial"
        elif not port:
            st.session_state["connected"] = False
            st.session_state["last_error"] = "No COM port selected."
        else:
            try:
                rdr = SerialReader(SerialConfig(port=port, baud=int(baud), timeout_s=1.0))
                rdr.start()
                st.session_state["reader"] = rdr
                st.session_state["connected"] = True

                if st.session_state["log_enabled"]:
                    folder = ensure_run_folder(st.session_state["log_folder"])
                    st.session_state["log_path"] = init_logfile(folder)

                msg = f"Connected to {port} @ {baud}"
                if st.session_state["log_enabled"]:
                    msg += f" | Logging to: {st.session_state['log_path']}"
                set_status(msg, "success")

            except Exception as e:
                st.session_state["connected"] = False
                st.session_state["reader"] = None
                st.session_state["last_error"] = str(e)

    if disconnect_clicked:
        if st.session_state["reader"] is not None:
            st.session_state["reader"].stop()
            st.session_state["reader"] = None
        st.session_state["connected"] = False
        set_status("Disconnected.", "info")

    if clear_clicked:
        st.session_state["df"] = pd.DataFrame(columns=DATA_COLUMNS)
        st.session_state["raw_lines"] = []
        st.session_state["t0_time_s"] = None
        set_status("Cleared in-memory plot data (logging file, if enabled, is unchanged).", "info")


def read_and_store_serial(enabled_channels, raw_keep, max_points):
    reader = st.session_state.get("reader")

    if st.session_state.get("last_error"):
        set_status("Could not connect. See error below.", "error")
        st.error(st.session_state["last_error"])

    if reader and st.session_state["connected"] and (not st.session_state["paused"]):
        lines = reader.get_lines(max_lines=2000)

        if lines:
            st.session_state["raw_lines"].extend(lines)
            st.session_state["raw_lines"] = st.session_state["raw_lines"][-raw_keep:]

            rows = []
            for line in lines:
                parsed = parse_cap_line(line)
                if parsed and parsed["channel"] in enabled_channels:
                    rows.append(parsed)

            if rows:
                df_new = pd.DataFrame(rows, columns=DATA_COLUMNS)

                new_min_t = float(df_new["time_s"].min())
                if st.session_state["t0_time_s"] is None:
                    st.session_state["t0_time_s"] = new_min_t
                elif new_min_t < float(st.session_state["t0_time_s"]):
                    st.session_state["t0_time_s"] = new_min_t

                if st.session_state["log_enabled"]:
                    try:
                        if not st.session_state.get("log_path"):
                            folder = ensure_run_folder(st.session_state["log_folder"])
                            st.session_state["log_path"] = init_logfile(folder)
                        append_rows_to_csv(st.session_state["log_path"], df_new)
                    except Exception as e:
                        st.session_state["last_error"] = f"Logging error: {e}"

                if st.session_state["df"].empty:
                    df_all = df_new.copy()
                else:
                    df_all = pd.concat([st.session_state["df"], df_new], ignore_index=True)

                if len(df_all) > max_points:
                    df_all = df_all.iloc[-max_points:].reset_index(drop=True)

                st.session_state["df"] = df_all


def filter_df_by_enabled_channels(enabled_channels):
    if enabled_channels:
        if not st.session_state["df"].empty:
            st.session_state["df"] = st.session_state["df"][
                st.session_state["df"]["channel"].isin(enabled_channels)
            ].copy()
    else:
        st.session_state["df"] = st.session_state["df"].iloc[0:0].copy()


def main():
    init_state()
    st.title("Arduino Live Grapher")

    sidebar_values = render_sidebar()

    auto_refresh = sidebar_values["auto_refresh"]
    refresh_ms = sidebar_values["refresh_ms"]
    max_points = sidebar_values["max_points"]
    time_unit = sidebar_values["time_unit"]
    smooth_mode = sidebar_values["smooth_mode"]
    rolling_window = sidebar_values["rolling_window"]
    ema_alpha = sidebar_values["ema_alpha"]
    display_unit = sidebar_values["display_unit"]
    autoscale_y = sidebar_values["autoscale_y"]
    y_pad_pct = sidebar_values["y_pad_pct"]
    show_raw = sidebar_values["show_raw"]
    raw_keep = sidebar_values["raw_keep"]
    window_seconds = sidebar_values["window_seconds"]
    fixed_y = sidebar_values["fixed_y"]
    y_min_manual = sidebar_values["y_min_manual"]
    y_max_manual = sidebar_values["y_max_manual"]
    plot_last_n = sidebar_values["plot_last_n"]
    chart_height = sidebar_values["chart_height"]

    enabled_channels = set()
    if st.session_state["collect_C1"]:
        enabled_channels.add("C1")
    if st.session_state["collect_C2"]:
        enabled_channels.add("C2")

    filter_df_by_enabled_channels(enabled_channels)

    ports = get_available_ports()
    controls = render_connection_controls(ports)

    port = controls["port"]
    baud = controls["baud"]
    connect_clicked = controls["connect_clicked"]
    disconnect_clicked = controls["disconnect_clicked"]
    clear_clicked = controls["clear_clicked"]

    handle_connection_actions(connect_clicked, disconnect_clicked, clear_clicked, port, baud)
    read_and_store_serial(enabled_channels, raw_keep, max_points)

    df = st.session_state["df"]

    left, right = st.columns([5, 1], gap="large")

    fig = render_plot_section(
        left,
        df,
        enabled_channels,
        time_unit,
        smooth_mode,
        rolling_window,
        ema_alpha,
        display_unit,
        autoscale_y,
        y_pad_pct,
        window_seconds,
        fixed_y,
        y_min_manual,
        y_max_manual,
        plot_last_n,
        chart_height,
    )

    render_latest_values_section(right, df, time_unit, display_unit)
    render_save_section(right, df, fig)
    render_raw_serial(show_raw, raw_keep)

    if auto_refresh and st.session_state.get("connected", False) and (not st.session_state["paused"]):
        time.sleep(refresh_ms / 1000.0)
        st.rerun()


if __name__ == "__main__":
    main()
