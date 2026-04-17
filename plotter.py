import os
from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from helpers import (
    TIME_SCALE,
    TIME_LABEL,
    PF_TO_UNIT,
    convert_pf_to_unit,
    seconds_to_hms_str,
)


def _make_hms_ticks(xmin, xmax, n_ticks=6):
    if xmax <= xmin:
        return [xmin], [seconds_to_hms_str(xmin)]

    tick_vals = np.linspace(xmin, xmax, n_ticks)
    tick_text = [seconds_to_hms_str(v) for v in tick_vals]
    return tick_vals.tolist(), tick_text


def render_plot_section(
    container,
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
):
    fig = None

    with container:
        st.subheader("Live Capacitance vs Time")

        if df.empty:
            st.info("No parsed data yet (or channels disabled). Example: 55.00s: C1 = 9.546 pF (ADC=287)")
            return None

        wide = (
            df.pivot_table(index="time_s", columns="channel", values="cap_pf", aggfunc="last")
            .sort_index()
            .reset_index()
        )

        if len(wide) > plot_last_n:
            wide = wide.iloc[-plot_last_n:].copy()

        plot_df = wide.copy()

        for ch in [c for c in plot_df.columns if c != "time_s"]:
            s = plot_df[ch]
            if smooth_mode == "Rolling mean":
                plot_df[ch] = s.rolling(rolling_window, min_periods=1).mean()
            elif smooth_mode == "EMA (exponential)":
                plot_df[ch] = s.ewm(alpha=ema_alpha, adjust=False).mean()

        t0 = st.session_state.get("t0_time_s")
        if t0 is None:
            t0 = float(plot_df["time_s"].min())

        plot_df["t_rel_s"] = plot_df["time_s"] - float(t0)

        xmax_s = float(plot_df["t_rel_s"].max()) if len(plot_df) else 0.0
        xmin_s = max(0.0, xmax_s - float(window_seconds))

        plot_df = plot_df[plot_df["t_rel_s"] >= xmin_s].copy()

        if plot_df.empty:
            st.info("No data in the current visible time window yet.")
            return None

        time_scale = TIME_SCALE[time_unit]
        unit_scale = PF_TO_UNIT.get(display_unit, 1.0)

        if time_unit == "HH:MM:SS":
            x = plot_df["t_rel_s"]
            x_title = TIME_LABEL[time_unit]
        else:
            x = plot_df["t_rel_s"] * time_scale
            x_title = TIME_LABEL[time_unit]

        fig = go.Figure()

        plotted_any = False
        y_all = []

        for ch in [c for c in plot_df.columns if c not in ["time_s", "t_rel_s"]]:
            y = plot_df[ch] * unit_scale

            if y.notna().any():
                plotted_any = True
                y_all.extend(y.dropna().tolist())

                fig.add_trace(
                    go.Scattergl(
                        x=x,
                        y=y,
                        mode="lines",
                        name=ch,
                        line=dict(width=2),
                        customdata=[seconds_to_hms_str(v) for v in plot_df["t_rel_s"]],
                        hovertemplate=(
                            f"{ch}<br>"
                            + "Time: %{customdata}<br>"
                            + f"Capacitance: %{{y:.4f}} {display_unit}<extra></extra>"
                        ),
                    )
                )

        if not plotted_any:
            st.info("No valid plotted channel data available.")
            return None

        fig.update_layout(
            title=dict(text="Capacitance vs Time", x=0.02, xanchor="left"),
            xaxis_title=x_title,
            yaxis_title=f"Capacitance ({display_unit})",
            template="plotly_white",
            height=chart_height,
            hovermode="x unified",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1.0,
            ),
            margin=dict(l=40, r=20, t=70, b=40),
            font=dict(size=15),
        )

        fig.update_xaxes(
            showgrid=True,
            gridwidth=1,
            zeroline=False,
        )
        fig.update_yaxes(
            showgrid=True,
            gridwidth=1,
            zeroline=False,
        )

        if time_unit == "HH:MM:SS":
            tick_vals, tick_text = _make_hms_ticks(xmin_s, xmax_s, n_ticks=6)
            fig.update_xaxes(
                range=[xmin_s, xmax_s],
                tickmode="array",
                tickvals=tick_vals,
                ticktext=tick_text,
            )
        else:
            xmin_disp = xmin_s * time_scale
            xmax_disp = xmax_s * time_scale
            fig.update_xaxes(range=[xmin_disp, xmax_disp])

        if fixed_y:
            fig.update_yaxes(range=[y_min_manual, y_max_manual])
        elif autoscale_y and len(y_all) > 0:
            y_min = min(y_all)
            y_max = max(y_all)

            if y_min == y_max:
                pad_y = 1.0
            else:
                pad_y = (y_max - y_min) * (y_pad_pct / 100.0)

            fig.update_yaxes(range=[y_min - pad_y, y_max + pad_y])

        st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})

        st.caption(
            f"In-memory points: {len(df)} | "
            f"Visible points: {len(plot_df)} | "
            f"Collecting: {', '.join(sorted(enabled_channels)) if enabled_channels else 'NONE'} | "
            f"Logging: {'ON' if st.session_state['log_enabled'] else 'OFF'}"
            + (
                f" → {st.session_state.get('log_path', '')}"
                if st.session_state["log_enabled"]
                else ""
            )
        )

    return fig


def render_latest_values_section(container, df, time_unit, display_unit):
    with container:
        st.subheader("Latest values")

        if df.empty:
            st.write("—")
            return

        latest = df.sort_values("time_s").groupby("channel").tail(1).sort_values("channel")

        t0 = st.session_state.get("t0_time_s")
        if t0 is None:
            t0 = float(df["time_s"].min())

        for _, r in latest.iterrows():
            ch = r["channel"]
            display_val = convert_pf_to_unit(r["cap_pf"], display_unit)

            st.metric(label=f"{ch} ({display_unit})", value=f"{display_val:.3f}", delta=None)

            t_rel = float(r["time_s"]) - float(t0)
            if time_unit == "HH:MM:SS":
                t_caption = f"t={seconds_to_hms_str(t_rel)}"
            else:
                time_scale = TIME_SCALE[time_unit]
                unit_label = time_unit[:-1] if time_unit.endswith("s") else time_unit
                t_caption = f"t={(t_rel * time_scale):.3f} {unit_label}"

            st.caption(
                f"{t_caption}, raw={r['cap_value']:.3f} {r['cap_unit']}"
                + (f", ADC={int(r['adc'])}" if pd.notna(r["adc"]) else "")
            )

        st.divider()


def render_save_section(container, df, fig):
    with container:
        st.subheader("Save / Download")

        run_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_folder = os.path.join(os.getcwd(), f"run_{run_stamp}")
        save_folder = st.text_input("Save folder (manual)", value=default_folder)

        c1, c2 = st.columns(2)

        with c1:
            if st.button("Save CSV to folder (manual)", use_container_width=True, disabled=df.empty):
                os.makedirs(save_folder, exist_ok=True)
                csv_path = os.path.join(save_folder, "arduino_data_in_memory.csv")
                df.to_csv(csv_path, index=False)
                st.success(f"Saved: {csv_path}")

        with c2:
            if st.button("Save Plot HTML to folder", use_container_width=True, disabled=(df.empty or fig is None)):
                os.makedirs(save_folder, exist_ok=True)
                html_path = os.path.join(save_folder, "arduino_plot.html")
                fig.write_html(html_path)
                st.success(f"Saved: {html_path}")

        if not df.empty:
            csv_bytes = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download CSV (in-memory only)",
                data=csv_bytes,
                file_name="arduino_data_in_memory.csv",
                mime="text/csv",
                use_container_width=True,
            )

            if fig is not None:
                html_bytes = fig.to_html().encode("utf-8")
                st.download_button(
                    "Download Plot (HTML)",
                    data=html_bytes,
                    file_name="arduino_plot.html",
                    mime="text/html",
                    use_container_width=True,
                )

            if st.session_state.get("log_enabled") and st.session_state.get("log_path"):
                st.info(f"Continuous logfile: {st.session_state['log_path']}")


def render_raw_serial(show_raw, raw_keep):
    if show_raw:
        with st.expander("Raw Serial (what Arduino is actually printing)", expanded=True):
            if st.session_state["raw_lines"]:
                st.code("\n".join(st.session_state["raw_lines"][-raw_keep:]), language="text")
            else:
                st.write("No raw serial received yet.")