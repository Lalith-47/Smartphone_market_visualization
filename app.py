import dash
from dash import dcc, html, dash_table, Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import base64, io

app = dash.Dash(__name__, title="Smartphone Market Trends")

# ─── Built-in Datasets ───────────────────────────────────────────────────────

DATASETS = {
    "Users by Region (2023)": pd.DataFrame({
        "Region":       ["Asia Pacific", "South Asia", "Europe", "Mid East & Africa", "Latin America", "North America"],
        "Users (B)":    [3.10, 0.92, 0.71, 0.47, 0.40, 0.33],
        "YoY Growth %": [4.2, 7.1, 1.8, 9.3, 3.5, 1.1],
    }),
    "OS Market Share (2023)": pd.DataFrame({
        "OS":        ["Android", "iOS", "KaiOS", "Others"],
        "Share %":   [71.8, 27.6, 0.3, 0.3],
        "Users (B)": [4.26, 1.64, 0.017, 0.017],
    }),
    "Age Distribution (2023)": pd.DataFrame({
        "Age Group": ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"],
        "Usage %":   [22, 30, 21, 13, 9, 5],
        "Users (M)": [1305, 1779, 1245, 771, 534, 297],
    }),
    "Brand Shipments Q3 2023": pd.DataFrame({
        "Brand":          ["Samsung", "Apple", "Xiaomi", "OPPO", "Vivo", "Others"],
        "Shipments (M)":  [53.5, 50.1, 35.8, 25.6, 23.4, 82.6],
        "Market Share %": [19.4, 18.2, 13.0, 9.3, 8.5, 30.0],
    }),
    "Global Users 2018-2024": pd.DataFrame({
        "Year":      [2018, 2019, 2020, 2021, 2022, 2023, 2024],
        "Users (B)": [3.2, 3.5, 3.9, 4.3, 4.9, 5.4, 6.1],
    }),
}

CHART_TYPES = ["Auto", "Bar", "Pie", "Line", "Scatter", "Area", "Histogram", "Treemap"]

# ─── Helper Functions ─────────────────────────────────────────────────────────

def get_df(src: str, uploaded_json, dataset_name: str):
    """Central data resolver. Returns DataFrame or None."""
    if src == "upload":
        if not uploaded_json:
            return None
        return pd.read_json(io.StringIO(uploaded_json), orient="split")
    return DATASETS.get(dataset_name)


def recommend_chart(df: pd.DataFrame) -> str:
    """Pick best chart type based on column types."""
    num_cols = df.select_dtypes(include="number").columns.tolist()
    cat_cols = df.select_dtypes(exclude="number").columns.tolist()
    has_time = any(kw in c.lower() for c in num_cols for kw in ["year", "date", "time"])
    if has_time:
        return "Line"
    if cat_cols and df[cat_cols[0]].nunique() <= 6 and len(num_cols) == 1:
        return "Pie"
    if len(num_cols) >= 2 and not cat_cols:
        return "Scatter"
    return "Bar"


def build_chart(df: pd.DataFrame, chart_type: str, title: str = "") -> go.Figure:
    """Build and return a Plotly figure."""
    num_cols = df.select_dtypes(include="number").columns.tolist()
    cat_cols = df.select_dtypes(exclude="number").columns.tolist()

    if not num_cols:
        return go.Figure()

    x_col = cat_cols[0] if cat_cols else num_cols[0]
    y_col = num_cols[0]
    base = dict(template="plotly", title=title)

    try:
        if chart_type == "Pie":
            fig = px.pie(df, names=x_col, values=y_col, title=title,
                         template="plotly", hole=0.3)
        elif chart_type == "Line":
            fig = px.line(df, x=x_col, y=y_col, markers=True, **base)
        elif chart_type == "Scatter":
            y2 = num_cols[1] if len(num_cols) > 1 else y_col
            fig = px.scatter(df, x=y_col, y=y2,
                             color=cat_cols[0] if cat_cols else None, **base)
        elif chart_type == "Area":
            fig = px.area(df, x=x_col, y=y_col, **base)
        elif chart_type == "Histogram":
            fig = px.histogram(df, x=y_col, **base)
        elif chart_type == "Treemap":
            if cat_cols:
                fig = px.treemap(df, path=[x_col], values=y_col,
                                 title=title, template="plotly")
            else:
                fig = px.bar(df, x=x_col, y=y_col, **base)
        else:  # Bar (default)
            fig = px.bar(df, x=x_col, y=y_col,
                         color=cat_cols[0] if cat_cols else None, **base)
    except Exception:
        fig = px.bar(df, x=x_col, y=y_col, **base)

    fig.update_layout(
        paper_bgcolor="#ffffff",
        plot_bgcolor="#f8fafc",
        font=dict(color="#1e293b"),
        margin=dict(l=40, r=40, t=55, b=40),
    )
    return fig


def make_table(df: pd.DataFrame) -> dash_table.DataTable:
    """Build a styled DataTable from a DataFrame."""
    return dash_table.DataTable(
        data=df.to_dict("records"),
        columns=[{"name": c, "id": c} for c in df.columns],
        page_size=10,
        sort_action="native",
        filter_action="native",
        style_table={"overflowX": "auto"},
        style_header={
            "backgroundColor": "#f1f5f9", "fontWeight": "700",
            "fontSize": "12px", "color": "#475569",
            "border": "none", "textTransform": "uppercase",
            "padding": "10px 14px",
        },
        style_cell={
            "fontSize": "13px", "color": "#1e293b",
            "padding": "10px 14px", "border": "none",
            "borderBottom": "1px solid #f1f5f9",
            "textAlign": "left", "backgroundColor": "#ffffff",
            "minWidth": "100px",
        },
        style_data_conditional=[
            {"if": {"row_index": "odd"}, "backgroundColor": "#f8fafc"},
        ],
        style_filter={
            "fontSize": "12px", "backgroundColor": "#f8fafc",
            "border": "none", "borderBottom": "1px solid #e2e8f0",
        },
    )


# ─── Style Constants ──────────────────────────────────────────────────────────

SIDEBAR_STYLE = {
    "width": "270px", "minWidth": "270px", "padding": "20px 16px",
    "background": "#ffffff", "borderRight": "1px solid #e2e8f0",
    "overflowY": "auto", "height": "calc(100vh - 68px)",
}
CARD = {
    "background": "#f8fafc", "borderRadius": "10px",
    "padding": "10px 12px", "marginBottom": "14px",
}
LABEL = {
    "fontSize": "12px", "color": "#64748b",
    "marginBottom": "6px", "fontWeight": "600", "margin": "0 0 6px 0",
}
UPLOAD_SHOW = {
    "display": "block", "width": "100%",
    "border": "2px dashed #94a3b8", "borderRadius": "8px",
    "padding": "16px 10px", "textAlign": "center", "cursor": "pointer",
    "fontSize": "13px", "color": "#64748b", "background": "#f8fafc",
    "marginBottom": "12px", "boxSizing": "border-box",
}
UPLOAD_HIDE = {"display": "none"}

# ─── Layout ───────────────────────────────────────────────────────────────────

app.layout = html.Div(style={
    "fontFamily": "Inter, sans-serif", "color": "#1e293b",
    "background": "#f1f5f9", "height": "100vh", "overflow": "hidden",
}, children=[

    # ── Header ───────────────────────────────────────────────────────────────
    html.Div(style={
        "display": "flex", "alignItems": "center", "gap": "12px",
        "padding": "14px 24px", "background": "#ffffff",
        "borderBottom": "1px solid #e2e8f0", "height": "68px",
        "boxSizing": "border-box",
    }, children=[
        html.Span("📱", style={"fontSize": "24px"}),
        html.Div([
            html.H3("Smartphone Market Trends",
                    style={"margin": 0, "fontSize": "18px", "fontWeight": "700"}),
            html.P("Interactive Visualization Dashboard",
                   style={"margin": 0, "fontSize": "12px", "color": "#64748b"}),
        ]),
    ]),

    html.Div(style={"display": "flex", "height": "calc(100vh - 68px)"}, children=[

        # ── Sidebar ──────────────────────────────────────────────────────────
        html.Div(style=SIDEBAR_STYLE, children=[

            # 1. Data Source
            html.Div(style=CARD, children=[
                html.P("DATA SOURCE", style=LABEL),
                dcc.RadioItems(
                    id="data-source", value="builtin",
                    options=[
                        {"label": "  Built-in data", "value": "builtin"},
                        {"label": "  Upload CSV",    "value": "upload"},
                    ],
                    labelStyle={"display": "block", "marginBottom": "6px", "fontSize": "13px"},
                ),
            ]),

            # 2. Upload widget (shown only in upload mode)
            dcc.Upload(
                id="upload-csv", accept=".csv", multiple=False,
                style=UPLOAD_HIDE,
                children=html.Div([
                    html.Div("📂", style={"fontSize": "28px", "marginBottom": "4px"}),
                    html.Span("Drop CSV here or "),
                    html.U("click to browse"),
                ]),
            ),

            # Upload feedback
            html.Div(id="upload-status",
                     style={"fontSize": "12px", "marginBottom": "10px", "display": "none"}),

            # 3. Built-in dataset selector
            html.Div(id="dataset-card", style=CARD, children=[
                html.P("DATASET", style=LABEL),
                dcc.Dropdown(
                    id="dataset-select", value="Users by Region (2023)", clearable=False,
                    options=[{"label": k, "value": k} for k in DATASETS],
                    style={"fontSize": "13px"},
                ),
            ]),

            # 4. Smart recommendation
            html.Div(id="rec-box", style={
                "background": "#eff6ff", "border": "1px solid #93c5fd",
                "borderRadius": "8px", "padding": "8px 12px",
                "marginBottom": "14px", "fontSize": "12px", "color": "#1d4ed8",
            }),

            # 5. Chart type
            html.Div(style=CARD, children=[
                html.P("CHART TYPE", style=LABEL),
                dcc.Dropdown(
                    id="chart-type", value="Auto", clearable=False,
                    options=[{"label": c, "value": c} for c in CHART_TYPES],
                    style={"fontSize": "13px"},
                ),
            ]),

            # 6. Filters
            html.Div(style=CARD, children=[
                html.P("FILTER", style=LABEL),
                html.P(id="filter-label",
                       style={"fontSize": "12px", "color": "#94a3b8", "marginBottom": "6px"}),
                dcc.Checklist(
                    id="row-filter",
                    labelStyle={"display": "block", "marginBottom": "4px", "fontSize": "13px"},
                ),
            ]),

            # 7. View mode
            html.Div(style=CARD, children=[
                html.P("VIEW MODE", style=LABEL),
                dcc.RadioItems(
                    id="view-mode", value="single",
                    options=[
                        {"label": "  Single chart",    "value": "single"},
                        {"label": "  Dashboard (all)", "value": "dashboard"},
                        {"label": "  Compare",         "value": "compare"},
                    ],
                    labelStyle={"display": "block", "marginBottom": "6px", "fontSize": "13px"},
                ),
            ]),

            # 8. Compare: second dataset
            html.Div(id="compare-section", style={"display": "none"}, children=[
                html.Div(style=CARD, children=[
                    html.P("COMPARE WITH", style=LABEL),
                    dcc.Dropdown(
                        id="compare-dataset", value="OS Market Share (2023)", clearable=False,
                        options=[{"label": k, "value": k} for k in DATASETS],
                        style={"fontSize": "13px"},
                    ),
                ]),
            ]),

            html.P("📷 Camera icon on chart toolbar → export PNG.",
                   style={"fontSize": "11px", "color": "#94a3b8", "marginTop": "4px"}),
        ]),

        # ── Main Content ─────────────────────────────────────────────────────
        html.Div(style={"flex": 1, "overflowY": "auto", "padding": "20px"}, children=[
            html.Div(id="main-content"),
            html.Div(id="data-preview", style={"marginTop": "20px"}),
        ]),
    ]),

    # Persistent store for uploaded CSV data
    dcc.Store(id="uploaded-df", storage_type="memory"),
])

# ─── Callbacks ────────────────────────────────────────────────────────────────

# CB1: Show/hide upload widget vs dataset dropdown
@app.callback(
    Output("upload-csv",   "style"),
    Output("dataset-card", "style"),
    Input("data-source",   "value"),
)
def toggle_source(src):
    if src == "upload":
        return UPLOAD_SHOW, {"display": "none"}
    return UPLOAD_HIDE, CARD


# CB2: Show/hide compare section
@app.callback(
    Output("compare-section", "style"),
    Input("view-mode", "value"),
)
def toggle_compare(mode):
    return {"display": "block"} if mode == "compare" else {"display": "none"}


# CB3: Parse and store uploaded CSV → also update status message
@app.callback(
    Output("uploaded-df",   "data"),
    Output("upload-status", "children"),
    Output("upload-status", "style"),
    Input("upload-csv",     "contents"),
    State("upload-csv",     "filename"),
    prevent_initial_call=True,
)
def store_upload(contents, filename):
    hide = {"display": "none"}
    if not contents:
        return None, "", hide
    try:
        header, b64data = contents.split(",", 1)        # safe split
        decoded = base64.b64decode(b64data).decode("utf-8", errors="replace")
        df = pd.read_csv(io.StringIO(decoded))
        if df.empty:
            raise ValueError("CSV is empty.")
        msg  = f"✅ {filename}  •  {len(df)} rows  •  {len(df.columns)} columns"
        show = {"fontSize": "12px", "color": "#16a34a", "marginBottom": "10px",
                "background": "#f0fdf4", "border": "1px solid #86efac",
                "borderRadius": "6px", "padding": "6px 10px"}
        return df.to_json(orient="split", date_format="iso"), msg, show
    except Exception as exc:
        msg  = f"❌ Error reading file: {exc}"
        show = {"fontSize": "12px", "color": "#dc2626", "marginBottom": "10px",
                "background": "#fef2f2", "border": "1px solid #fca5a5",
                "borderRadius": "6px", "padding": "6px 10px"}
        return None, msg, show


# CB4: Update sidebar info (rec-box + filter controls)
#      Triggered by any data-relevant change
@app.callback(
    Output("rec-box",      "children"),
    Output("row-filter",   "options"),
    Output("row-filter",   "value"),
    Output("filter-label", "children"),
    Input("data-source",   "value"),
    Input("uploaded-df",   "data"),
    Input("dataset-select","value"),
)
def update_sidebar(src, uploaded_json, dataset_name):
    df = get_df(src, uploaded_json, dataset_name)

    # No data yet
    if df is None:
        placeholder = "💡 Upload a CSV to see recommendation." if src == "upload" \
                      else "💡 Select a dataset."
        return placeholder, [], [], "No data loaded."

    rec      = recommend_chart(df)
    rec_text = f"💡 Recommended chart: {rec}"

    cat_cols = df.select_dtypes(exclude="number").columns.tolist()
    if not cat_cols:
        return rec_text, [], [], "No categorical column to filter on."

    col  = cat_cols[0]
    vals = sorted(df[col].dropna().unique().tolist(), key=str)
    opts = [{"label": str(v), "value": v} for v in vals]
    return rec_text, opts, vals, f"Filtering by: {col}"


# CB5: Render main chart(s) + data preview table
#      All chart-related inputs flow into a single callback — no chaining issues
@app.callback(
    Output("main-content", "children"),
    Output("data-preview", "children"),
    Input("data-source",    "value"),
    Input("uploaded-df",    "data"),
    Input("dataset-select", "value"),
    Input("chart-type",     "value"),
    Input("view-mode",      "value"),
    Input("compare-dataset","value"),
    Input("row-filter",     "value"),
)
def render_main(src, uploaded_json, dataset_name, chart_type, mode, compare_name, filter_vals):
    cfg = dict(config={"displaylogo": False})

    # ── No upload yet ─────────────────────────────────────────────────────
    if src == "upload" and not uploaded_json:
        placeholder = html.Div([
            html.Div("📂", style={"fontSize": "56px", "marginBottom": "16px"}),
            html.P("Upload a CSV file to visualize your data.",
                   style={"color": "#64748b", "fontSize": "15px", "margin": 0}),
            html.P("Supported: any CSV with at least one numeric column.",
                   style={"color": "#94a3b8", "fontSize": "13px", "marginTop": "6px"}),
        ], style={
            "textAlign": "center", "padding": "100px 40px",
            "background": "#ffffff", "borderRadius": "12px",
            "border": "2px dashed #e2e8f0",
        })
        return placeholder, None

    # ── Resolve primary dataframe ─────────────────────────────────────────
    df = get_df(src, uploaded_json, dataset_name)
    if df is None:
        err = html.P("⚠️ Could not load data.", style={"color": "#dc2626", "padding": "20px"})
        return err, None

    title = "Uploaded CSV" if src == "upload" else dataset_name

    # ── Apply checklist filter ────────────────────────────────────────────
    cat_cols = df.select_dtypes(exclude="number").columns.tolist()
    if cat_cols and filter_vals:
        df = df[df[cat_cols[0]].isin(filter_vals)]
        if df.empty:
            warn = html.P("⚠️ All rows filtered out. Adjust the filter.",
                          style={"color": "#b45309", "padding": "20px"})
            return warn, None

    actual_chart = chart_type if chart_type != "Auto" else recommend_chart(df)

    # ── Data preview table (only for uploads) ─────────────────────────────
    full_df   = get_df(src, uploaded_json, dataset_name)  # unfiltered
    preview   = None
    if src == "upload" and uploaded_json and full_df is not None:
        preview = html.Div([
            html.Div(style={
                "display": "flex", "justifyContent": "space-between",
                "alignItems": "center", "marginBottom": "12px",
            }, children=[
                html.H4("📋 Data Preview", style={"margin": 0, "fontSize": "15px"}),
                html.Span(
                    f"{len(full_df)} rows × {len(full_df.columns)} columns",
                    style={"fontSize": "12px", "color": "#64748b"},
                ),
            ]),
            make_table(full_df),
        ], style={
            "background": "#ffffff", "borderRadius": "10px",
            "padding": "16px", "boxShadow": "0 1px 4px rgba(0,0,0,0.06)",
        })

    # ── Dashboard mode ────────────────────────────────────────────────────
    if mode == "dashboard":
        cards = []
        data_source = DATASETS if src == "builtin" else {title: df}
        for ds_name, ds_df in data_source.items():
            ct  = recommend_chart(ds_df)
            fig = build_chart(ds_df, ct, title=ds_name)
            cards.append(html.Div(
                dcc.Graph(figure=fig, **cfg),
                style={"width": "calc(50% - 10px)", "background": "#ffffff",
                       "borderRadius": "10px", "overflow": "hidden",
                       "boxShadow": "0 1px 4px rgba(0,0,0,0.06)"},
            ))
        # If built-in, show all 5 datasets
        if src == "builtin":
            content = html.Div(cards, style={"display": "flex", "flexWrap": "wrap", "gap": "20px"})
        else:
            content = html.Div(cards, style={"display": "flex", "flexWrap": "wrap", "gap": "20px"})
        return content, preview

    # ── Compare mode ──────────────────────────────────────────────────────
    elif mode == "compare":
        df2   = DATASETS.get(compare_name, list(DATASETS.values())[1])
        fig1  = build_chart(df,  actual_chart,          title=title)
        fig2  = build_chart(df2, recommend_chart(df2),  title=compare_name)
        panel = lambda fig, t: html.Div([
            html.P(t, style={"fontSize": "13px", "color": "#64748b",
                             "margin": "0 0 6px 0", "fontWeight": "600"}),
            dcc.Graph(figure=fig, **cfg),
        ], style={"width": "calc(50% - 10px)", "background": "#ffffff",
                  "borderRadius": "10px", "padding": "14px",
                  "boxShadow": "0 1px 4px rgba(0,0,0,0.06)"})
        content = html.Div([panel(fig1, title), panel(fig2, compare_name)],
                           style={"display": "flex", "gap": "20px"})
        return content, preview

    # ── Single chart mode ─────────────────────────────────────────────────
    else:
        fig = build_chart(df, actual_chart, title=title)
        content = html.Div(
            dcc.Graph(figure=fig, style={"height": "70vh"}, **cfg),
            style={"background": "#ffffff", "borderRadius": "10px",
                   "padding": "14px", "boxShadow": "0 1px 4px rgba(0,0,0,0.06)"},
        )
        return content, preview


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050)