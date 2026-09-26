from ui_theme import apply_theme
import streamlit as st
from team_preferences import opening_team

apply_theme()

st.title("Baseball Analytics Portfolio")

if opening_team():
    st.info(f"Opening team: {opening_team()}. All MLB teams remain available in the page selectors.")

st.write(
    """
    Welcome to my baseball analytics portfolio.

    This website presents four projects focused on player evaluation,
    scouting, predictive modeling, and baseball operations decision-making.
    """
)

st.header("Portfolio Projects")

st.markdown(
    """
    1. **Advanced Scouting Report Generator**
    2. **Pitcher Arsenal / Stuff Model**
    3. **Batter-Pitcher Matchup Predictor**
    4. **Scouting Comparison Tool**
    """
)

st.header("Goal")

st.write(
    """
    The goal of this portfolio is to demonstrate practical baseball analytics
    skills using Python, R, SQL, data visualization, statistical modeling, and
    clear communication.
    """
)
