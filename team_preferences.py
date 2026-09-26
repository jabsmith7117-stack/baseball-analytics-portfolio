"""Keep an optional opening team across Streamlit page navigation."""

import streamlit as st


def opening_team_index(options):
    preferred = st.session_state.get("portfolio_opening_team")
    return options.index(preferred) if preferred in options else 0


def opening_team():
    return st.session_state.get("portfolio_opening_team")
