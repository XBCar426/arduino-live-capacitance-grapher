import os
from datetime import datetime
import pandas as pd


DISPLAY_UNITS = ["pF", "nF", "uF", "mF", "F"]

PF_TO_UNIT = {
    "pF": 1.0,
    "nF": 1.0 / 1e3,
    "uF": 1.0 / 1e6,
    "mF": 1.0 / 1e9,
    "F": 1.0 / 1e12,
}

TIME_UNITS = ["HH:MM:SS", "seconds", "minutes", "hours"]

TIME_SCALE = {
    "HH:MM:SS": 1.0,
    "seconds": 1.0,
    "minutes": 1.0 / 60.0,
    "hours": 1.0 / 3600.0,
}

TIME_LABEL = {
    "HH:MM:SS": "Time (HH:MM:SS)",
    "seconds": "Time (s)",
    "minutes": "Time (min)",
    "hours": "Time (hr)",
}

DATA_COLUMNS = ["time_s", "channel", "cap_pf", "cap_value", "cap_unit", "adc"]


def convert_pf_to_unit(x_pf: float, unit: str) -> float:
    return float(x_pf) * PF_TO_UNIT.get(unit, 1.0)


def seconds_to_hms_str(total_seconds: float) -> str:
    if total_seconds is None or pd.isna(total_seconds):
        return ""
    s = int(round(float(total_seconds)))
    if s < 0:
        s = 0
    h = s // 3600
    m = (s % 3600) // 60
    sec = s % 60
    return f"{h:02d}:{m:02d}:{sec:02d}"


def ensure_run_folder(folder: str) -> str:
    os.makedirs(folder, exist_ok=True)
    return folder


def init_logfile(folder: str) -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(folder, f"arduino_log_{stamp}.csv")


def append_rows_to_csv(csv_path: str, df_rows: pd.DataFrame):
    file_exists = os.path.exists(csv_path)
    df_rows.to_csv(csv_path, mode="a", index=False, header=not file_exists)