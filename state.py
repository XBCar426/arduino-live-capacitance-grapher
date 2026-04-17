import streamlit as st
import pandas as pd
from helpers import DATA_COLUMNS


def init_state():
    st.session_state.setdefault("reader", None)
    st.session_state.setdefault("connected", False)
    st.session_state.setdefault("df", pd.DataFrame(columns=DATA_COLUMNS))
    st.session_state.setdefault("raw_lines", [])
    st.session_state.setdefault("paused", False)
    st.session_state.setdefault("last_error", "")
    st.session_state.setdefault("log_enabled", False)
    st.session_state.setdefault("log_folder", "")
    st.session_state.setdefault("log_path", "")
    st.session_state.setdefault("collect_C1", True)
    st.session_state.setdefault("collect_C2", True)
    st.session_state.setdefault("t0_time_s", None)