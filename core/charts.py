import plotly.graph_objects as go

SPIDER_LABELS_HE = [
    "אתגרי יומיום",
    "איזון עבודה-חיים",
    "פיתוח מקצועי",
    "גמול חומרי",
    "יחסים",
    "ביטחון תעסוקתי",
    "תרבות",
    "משמעות",
    "מימוש עצמי",
    "השפעה",
]

SPIDER_KEYS = [
    "daily_challenges",
    "work_life_balance",
    "professional_development",
    "compensation",
    "relationships",
    "security",
    "culture",
    "meaning",
    "self_actualization",
    "influence",
]


def create_spider_chart(spider_data: dict, client_name: str, lang: str = "he") -> go.Figure:
    values = [spider_data.get(k, 0) for k in SPIDER_KEYS]
    labels = SPIDER_LABELS_HE

    values_closed = values + [values[0]]
    labels_closed = labels + [labels[0]]

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=labels_closed,
        fill="toself",
        fillcolor="rgba(99, 110, 250, 0.2)",
        line=dict(color="rgb(99, 110, 250)", width=2),
        name=client_name,
        hovertemplate="%{theta}: %{r}/10<extra></extra>",
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10],
                tickfont=dict(size=10),
                gridcolor="rgba(0,0,0,0.1)",
            ),
            angularaxis=dict(
                tickfont=dict(size=12, family="Arial"),
                direction="clockwise",
            ),
            bgcolor="rgba(255,255,255,0)",
        ),
        showlegend=False,
        title=dict(
            text=f"פרופיל שביעות רצון — {client_name}" if lang == "he" else f"Satisfaction Profile — {client_name}",
            font=dict(size=16),
            x=0.5,
        ),
        paper_bgcolor="rgba(255,255,255,0)",
        height=450,
        margin=dict(t=60, b=40, l=60, r=60),
    )

    return fig


def create_energy_bars(energy_data: dict, lang: str = "he") -> go.Figure:
    labels = {
        "connection": "חיבור" if lang == "he" else "Connection",
        "progress": "התקדמות" if lang == "he" else "Progress",
        "influence": "השפעה" if lang == "he" else "Influence",
    }
    colors = {
        "connection": "#636EFA",
        "progress": "#EF553B",
        "influence": "#00CC96",
    }

    keys = list(labels.keys())
    bar_labels = [labels[k] for k in keys]
    bar_values = [energy_data.get(k, 0) for k in keys]
    bar_colors = [colors[k] for k in keys]

    fig = go.Figure(go.Bar(
        x=bar_labels,
        y=bar_values,
        marker_color=bar_colors,
        text=[f"{v}/10" for v in bar_values],
        textposition="outside",
        hovertemplate="%{x}: %{y}/10<extra></extra>",
    ))

    fig.update_layout(
        title=dict(
            text="מצברי אנרגיה" if lang == "he" else "Energy Batteries",
            font=dict(size=16),
            x=0.5,
        ),
        yaxis=dict(range=[0, 11], title="רמה" if lang == "he" else "Level"),
        paper_bgcolor="rgba(255,255,255,0)",
        plot_bgcolor="rgba(255,255,255,0)",
        height=300,
        margin=dict(t=60, b=40, l=40, r=40),
    )

    return fig
