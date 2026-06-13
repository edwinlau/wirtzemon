# pages/2_Backtest.py
# FPL Backtesting Dashboard

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from supabase import create_client, Client

st.set_page_config(
    page_title="FPL Backtest Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .metric-container {
        background: linear-gradient(90deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
        margin-bottom: 1rem;
    }
    .filter-section {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border: 1px solid #dee2e6;
    }
    .section-header {
        font-size: 1.4rem;
        font-weight: 600;
        color: #343a40;
        border-bottom: 2px solid #1f77b4;
        padding-bottom: 0.3rem;
        margin-bottom: 1rem;
    }
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_resource
def init_supabase() -> Client:
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception as exc:
        st.error(f"Database connection failed: {exc}")
        return None


supabase = init_supabase()

SEASON_LABELS = ["2023-24", "2024-25", "2025-26"]

# Estimated average FPL manager score per gameweek (benchmark)
AVG_MANAGER_GW_SCORE = {
    "2023-24": 51.3,
    "2024-25": 52.0,
    "2025-26": 52.0,
}

POSITION_SLOTS = {"GK": 2, "DEF": 5, "MID": 5, "FWD": 3}
BUDGET = 100.0  # £m


@st.cache_data(ttl=300)
def load_gw_history(seasons: tuple) -> pd.DataFrame:
    """Load players_gw_history rows for the requested seasons."""
    if not supabase:
        return pd.DataFrame()
    try:
        result = (
            supabase.table("players_gw_history")
            .select("*")
            .in_("season", list(seasons))
            .execute()
        )
        if not result.data:
            return pd.DataFrame()
        df = pd.DataFrame(result.data)
        for col in ["total_points", "minutes", "goals_scored", "assists",
                    "clean_sheets", "bonus", "bps", "value", "selected",
                    "transfers_in", "transfers_out", "gameweek"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        for col in ["influence", "creativity", "threat", "ict_index"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
        df["price"] = df["value"] / 10.0
        return df
    except Exception as exc:
        st.error(f"Error loading GW history: {exc}")
        return pd.DataFrame()


st.markdown('<div class="main-header">📈 FPL Backtesting Dashboard</div>', unsafe_allow_html=True)
st.markdown("Analyse historical performance, validate metrics, and simulate FPL strategies.")

with st.sidebar:
    st.header("Global Filters")
    selected_seasons = st.multiselect(
        "Seasons to analyse",
        options=SEASON_LABELS,
        default=["2023-24", "2024-25"],
    )
    if not selected_seasons:
        st.warning("Select at least one season.")
        st.stop()

with st.spinner("Loading GW history data..."):
    df_all = load_gw_history(tuple(selected_seasons))

if df_all.empty:
    st.error(
        "No data found in `players_gw_history` for the selected seasons. "
        "Run `scripts/backfill_historical.py` first."
    )
    st.stop()

# --- Section A: Data Overview ---

st.markdown('<div class="section-header">Section A — Data Overview</div>', unsafe_allow_html=True)

seasons_loaded = df_all["season"].nunique()
total_records = len(df_all)
gw_min = int(df_all["gameweek"].min())
gw_max = int(df_all["gameweek"].max())

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Seasons loaded", seasons_loaded)
with col2:
    st.metric("Total GW records", f"{total_records:,}")
with col3:
    st.metric("GW range covered", f"GW {gw_min} - GW {gw_max}")

avg_pts_gw = (
    df_all.groupby(["season", "gameweek"])["total_points"]
    .mean()
    .reset_index()
    .rename(columns={"total_points": "avg_points"})
)
avg_pts_gw["avg_points"] = avg_pts_gw["avg_points"].round(2)

fig_overview = px.line(
    avg_pts_gw,
    x="gameweek",
    y="avg_points",
    color="season",
    markers=True,
    title="Average Player Points per Gameweek",
    labels={"gameweek": "Gameweek", "avg_points": "Avg Points", "season": "Season"},
    template="plotly_white",
)
st.plotly_chart(fig_overview, use_container_width=True)

# --- Section B: Metric Accuracy ---

st.markdown('<div class="section-header">Section B — Metric Accuracy</div>', unsafe_allow_html=True)
st.write(
    "For each gameweek, players are ranked by a chosen metric from the **previous** GW. "
    "We check whether the top quartile outperformed the bottom quartile in the **next** GW."
)

metric_options = {
    "Value Score (pts / price)": "value_score",
    "ICT Index": "ict_index",
    "Form (total_points last GW)": "total_points",
}
metric_label = st.selectbox("Metric to analyse", list(metric_options.keys()))
metric_col = metric_options[metric_label]

df_lag = df_all.sort_values(["season", "element", "gameweek"]).copy()
df_lag["value_score"] = np.where(df_lag["price"] > 0, df_lag["total_points"] / df_lag["price"], 0.0)
df_lag["prev_metric"] = df_lag.groupby(["season", "element"])[metric_col].shift(1)
df_lag["next_points"] = df_lag.groupby(["season", "element"])["total_points"].shift(-1)
df_lag_clean = df_lag.dropna(subset=["prev_metric", "next_points"])

if df_lag_clean.empty:
    st.warning("Not enough data to compute metric accuracy. Need at least 2 GWs.")
else:
    def assign_quartile(group):
        group = group.copy()
        group["quartile"] = pd.qcut(
            group["prev_metric"], q=4,
            labels=["Q1 (Bottom)", "Q2", "Q3", "Q4 (Top)"],
            duplicates="drop",
        )
        return group

    df_quartile = (
        df_lag_clean.groupby(["season", "gameweek"], group_keys=False).apply(assign_quartile)
    )
    df_quartile = df_quartile.dropna(subset=["quartile"])

    avg_by_quartile = (
        df_quartile.groupby("quartile")["next_points"]
        .mean()
        .reset_index()
        .rename(columns={"next_points": "avg_next_gw_points"})
    )
    avg_by_quartile["avg_next_gw_points"] = avg_by_quartile["avg_next_gw_points"].round(2)

    fig_metric = px.bar(
        avg_by_quartile,
        x="quartile",
        y="avg_next_gw_points",
        color="quartile",
        title=f"Avg Next-GW Points by {metric_label} Quartile",
        labels={"quartile": "Quartile", "avg_next_gw_points": "Avg Next GW Points"},
        template="plotly_white",
        color_discrete_sequence=px.colors.sequential.Blues_r,
    )
    fig_metric.update_layout(showlegend=False)
    st.plotly_chart(fig_metric, use_container_width=True)

    if len(avg_by_quartile) >= 2:
        top_val = avg_by_quartile[avg_by_quartile["quartile"] == "Q4 (Top)"]["avg_next_gw_points"].values
        bot_val = avg_by_quartile[avg_by_quartile["quartile"] == "Q1 (Bottom)"]["avg_next_gw_points"].values
        if len(top_val) and len(bot_val):
            delta = float(top_val[0]) - float(bot_val[0])
            st.info(
                f"Top-quartile players scored **{delta:+.2f} pts** more on average "
                f"than bottom-quartile players in the following GW."
            )

# --- Section C: Strategy Simulator ---

st.markdown('<div class="section-header">Section C — Strategy Simulator</div>', unsafe_allow_html=True)

sim_col1, sim_col2, sim_col3 = st.columns(3)
with sim_col1:
    sim_season = st.selectbox("Season to simulate", options=selected_seasons, key="sim_season")
with sim_col2:
    strategy_metric_label = st.selectbox(
        "Pick players by metric",
        ["Value Score (pts / price)", "ICT Index", "Total Points (prev GW)"],
        key="sim_metric",
    )
with sim_col3:
    top_n_per_pos = st.number_input(
        "Top N candidates per position", min_value=5, max_value=50, value=20, step=5, key="sim_topn"
    )

sim_metric_map = {
    "Value Score (pts / price)": "value_score",
    "ICT Index": "ict_index",
    "Total Points (prev GW)": "total_points",
}
sim_metric_col = sim_metric_map[strategy_metric_label]

df_sim_season = df_all[df_all["season"] == sim_season].copy()
df_sim_season["value_score"] = np.where(
    df_sim_season["price"] > 0, df_sim_season["total_points"] / df_sim_season["price"], 0.0
)

gameweeks_sim = sorted(df_sim_season["gameweek"].unique())

if len(gameweeks_sim) < 2:
    st.warning("Need at least 2 GWs of data in this season to simulate.")
else:
    cumulative_sim_pts = []
    cumulative_avg_pts = []
    running_sim = 0
    running_avg = 0
    bench_per_gw = AVG_MANAGER_GW_SCORE.get(sim_season, 52.0)

    for gw in gameweeks_sim[1:]:  # start from GW2 so we have prev-GW data
        prev_gw = gw - 1
        prev_df = df_sim_season[df_sim_season["gameweek"] == prev_gw]
        curr_df = df_sim_season[df_sim_season["gameweek"] == gw].set_index("element")

        if prev_df.empty or curr_df.empty:
            running_avg += bench_per_gw
        else:
            selected_elements = []
            total_cost = 0.0
            for pos, slots in POSITION_SLOTS.items():
                pos_prev = prev_df[prev_df["position"] == pos].sort_values(
                    sim_metric_col, ascending=False
                ).head(top_n_per_pos)
                chosen = []
                for _, player_row in pos_prev.iterrows():
                    cost = player_row["price"] if player_row["price"] > 0 else 4.5
                    if total_cost + cost <= BUDGET and len(chosen) < slots:
                        chosen.append(player_row["element"])
                        total_cost += cost
                selected_elements.extend(chosen)
            gw_pts = sum(
                int(curr_df.loc[el, "total_points"])
                for el in selected_elements
                if el in curr_df.index
            )
            running_sim += gw_pts
            running_avg += bench_per_gw

        cumulative_sim_pts.append(running_sim)
        cumulative_avg_pts.append(running_avg)

    sim_df = pd.DataFrame({
        "gameweek": gameweeks_sim[1:],
        "Simulated Strategy": cumulative_sim_pts,
        f"Avg Manager (~{bench_per_gw} pts/GW)": cumulative_avg_pts,
    })
    sim_melt = sim_df.melt("gameweek", var_name="Series", value_name="Cumulative Points")

    fig_sim = px.line(
        sim_melt, x="gameweek", y="Cumulative Points", color="Series", markers=True,
        title=f"Strategy Simulator — {sim_season} | Metric: {strategy_metric_label}",
        labels={"gameweek": "Gameweek"},
        template="plotly_white",
    )
    st.plotly_chart(fig_sim, use_container_width=True)

    final_sim = cumulative_sim_pts[-1] if cumulative_sim_pts else 0
    final_avg = cumulative_avg_pts[-1] if cumulative_avg_pts else 0
    st.metric(
        "Final season points (strategy vs benchmark)",
        f"{final_sim:,} pts",
        delta=f"{final_sim - final_avg:+,} vs avg manager",
    )
    st.caption(
        "Strategy picks 15 players (2 GK, 5 DEF, 5 MID, 3 FWD) within £100m budget "
        "using only data available at the start of each GW (no lookahead)."
    )

# --- Section D: Player Drill-down ---

st.markdown('<div class="section-header">Section D — Player Drill-down</div>', unsafe_allow_html=True)

player_names = sorted(df_all["name"].dropna().unique().tolist())
search_player = st.selectbox(
    "Search for a player",
    options=["— select a player —"] + player_names,
    index=0,
    key="drilldown_player",
)

if search_player and search_player != "— select a player —":
    df_player = df_all[df_all["name"] == search_player].sort_values(["season", "gameweek"]).copy()
    if df_player.empty:
        st.warning(f"No GW history found for '{search_player}'.")
    else:
        df_player["gw_label"] = df_player["season"] + " GW" + df_player["gameweek"].astype(int).astype(str)
        tab_pts, tab_price, tab_sel = st.tabs(["Points per GW", "Price over time", "Selected"])

        with tab_pts:
            fig_pts = px.bar(
                df_player, x="gw_label", y="total_points", color="season",
                title=f"{search_player} — Points per Gameweek",
                labels={"gw_label": "Gameweek", "total_points": "Points"},
                template="plotly_white",
            )
            fig_pts.update_xaxes(tickangle=45)
            st.plotly_chart(fig_pts, use_container_width=True)

        with tab_price:
            fig_price = px.line(
                df_player, x="gw_label", y="price", color="season", markers=True,
                title=f"{search_player} — Price (£m) over Gameweeks",
                labels={"gw_label": "Gameweek", "price": "Price (£m)"},
                template="plotly_white",
            )
            fig_price.update_xaxes(tickangle=45)
            st.plotly_chart(fig_price, use_container_width=True)

        with tab_sel:
            if "selected" in df_player.columns:
                fig_sel = px.line(
                    df_player, x="gw_label", y="selected", color="season", markers=True,
                    title=f"{search_player} — Selected over Gameweeks",
                    labels={"gw_label": "Gameweek", "selected": "Selected"},
                    template="plotly_white",
                )
                fig_sel.update_xaxes(tickangle=45)
                st.plotly_chart(fig_sel, use_container_width=True)
            else:
                st.info("Selected data not available.")

        with st.expander("Raw data table"):
            st.dataframe(
                df_player[[
                    "season", "gameweek", "total_points", "minutes",
                    "goals_scored", "assists", "clean_sheets", "bonus",
                    "price", "ict_index",
                ]].reset_index(drop=True),
                use_container_width=True,
            )
else:
    st.info("Select a player above to see their GW-by-GW history.")

st.markdown("---")
col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    st.markdown("📊 **Historical backtesting**")
with col_f2:
    st.markdown("🔬 **Metric validation**")
with col_f3:
    st.markdown("⚽ **Strategy simulation**")
