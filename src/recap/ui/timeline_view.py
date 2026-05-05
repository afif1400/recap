"""Render a Patient's events as an interactive Plotly timeline.

X-axis is time, Y-axis groups events by category (lab, visit, scan, …).
Hovering a marker shows the event title and source. Clicking is wired
up later to scroll the chat to the relevant citation.
"""

import pandas as pd
import plotly.express as px

from recap.models import Patient

# Stable category order — controls the y-axis lane positions.
CATEGORY_ORDER = [
    "diagnosis",
    "visit",
    "lab",
    "report",
    "scan",
    "procedure",
    "med",
    "note",
    "photo",
    "other",
]

# Color per category — chosen for legibility on dark theme + colorblind-friendly.
CATEGORY_COLORS = {
    "diagnosis": "#e63946",
    "visit": "#2a9d8f",
    "lab": "#457b9d",
    "report": "#264653",
    "scan": "#f4a261",
    "procedure": "#9b5de5",
    "med": "#e76f51",
    "note": "#6c757d",
    "photo": "#bdb2ff",
    "other": "#adb5bd",
}


def build_timeline_figure(patient: Patient):
    """Return a Plotly Figure (or None if patient has no events)."""
    if not patient.events:
        return None

    df = pd.DataFrame([
        {
            "date": e.date,
            "category": e.category,
            "title": e.title,
            "source": e.source,
            "year": e.date.year,
        }
        for e in patient.events
    ])

    fig = px.scatter(
        df,
        x="date",
        y="category",
        color="category",
        category_orders={"category": CATEGORY_ORDER},
        color_discrete_map=CATEGORY_COLORS,
        hover_data={"title": True, "source": True, "category": False, "date": "|%Y-%m-%d"},
        title=f"{patient.display_name} — {len(patient.events)} events",
    )
    fig.update_traces(marker=dict(size=11, opacity=0.85, line=dict(width=0.5, color="white")))
    fig.update_layout(
        height=340,
        margin=dict(t=50, b=40, l=40, r=20),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis_title=None,
        yaxis_title=None,
    )
    return fig
