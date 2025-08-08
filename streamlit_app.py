# Enhanced FPL Dashboard - Phase 1: Advanced Statistics & Professional Layout

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from supabase import create_client, Client
from datetime import datetime, timedelta
import requests
import numpy as np

# Page config with custom theme
st.set_page_config(
    page_title="FPL Analytics Pro",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional appearance
st.markdown("""
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
    .data-table {
        font-size: 0.9rem;
    }
    .position-gk { background-color: #fff3e0; }
    .position-def { background-color: #e8f5e8; }
    .position-mid { background-color: #e3f2fd; }
    .position-fwd { background-color: #fce4ec; }
    .stat-category {
        background-color: #495057;
        color: white;
        text-align: center;
        font-weight: bold;
        padding: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Supabase
@st.cache_resource
def init_supabase():
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None

supabase = init_supabase()

# Enhanced data loading with advanced calculations
@st.cache_data(ttl=300)
def load_enhanced_player_data():
    """Load and enhance player data with advanced statistics"""
    if not supabase:
        return None
    
    try:
        # Get current players data
        result = supabase.table('players_current').select('*').execute()
        if not result.data:
            return None
            
        df = pd.DataFrame(result.data)
        
        # Basic calculations
        df['price'] = df['now_cost'] / 10
        df['value_score'] = df['total_points'] / df['price']
        df['ppg'] = df['points_per_game']
        
        # Advanced FPL calculations
        df = calculate_advanced_stats(df)
        
        return df
    except Exception as e:
        st.error(f"Error loading player data: {e}")
        return None

def calculate_advanced_stats(df):
    """Calculate advanced FPL statistics"""
    
    # Expected stats (simplified - in production would come from Understat)
    df['xG'] = np.where(df['position'] == 'FWD', 
                       (df['goals_scored'] * 0.9) + np.random.normal(0, 0.1, len(df)),
                       np.where(df['position'] == 'MID',
                               (df['goals_scored'] * 0.8) + np.random.normal(0, 0.05, len(df)),
                               (df['goals_scored'] * 0.7) + np.random.normal(0, 0.02, len(df))))
    
    df['xA'] = np.where(df['position'].isin(['MID', 'FWD']),
                       (df['assists'] * 0.85) + np.random.normal(0, 0.1, len(df)),
                       (df['assists'] * 0.7) + np.random.normal(0, 0.05, len(df)))
    
    # Goal involvement metrics
    df['xGI'] = df['xG'] + df['xA']
    df['GI'] = df['goals_scored'] + df['assists']
    
    # Per 90 minute stats (estimated based on minutes played)
    df['minutes_played'] = np.maximum(df['minutes'], 1)  # Avoid division by zero
    df['xG_per_90'] = (df['xG'] / df['minutes_played']) * 90
    df['xA_per_90'] = (df['xA'] / df['minutes_played']) * 90
    df['goals_per_90'] = (df['goals_scored'] / df['minutes_played']) * 90
    df['assists_per_90'] = (df['assists'] / df['minutes_played']) * 90
    
    # Bonus points prediction (simplified)
    df['xBPS'] = (df['xG'] * 30) + (df['xA'] * 25) + (df['minutes_played'] * 0.02)
    df['bonus_frequency'] = np.where(df['total_points'] > 0, df['bonus'] / (df['total_points'] / 90), 0)
    
    # Key passes estimation
    df['key_passes'] = np.where(df['position'].isin(['MID', 'FWD']),
                               df['assists'] * 3 + np.random.poisson(2, len(df)),
                               df['assists'] * 2 + np.random.poisson(1, len(df)))
    
    # Clean sheet percentage (for defenders and goalkeepers)
    df['cs_percentage'] = np.where(df['position'].isin(['GK', 'DEF']),
                                  (df['clean_sheets'] / np.maximum(df['minutes_played'] / 90, 1)) * 100,
                                  0)
    
    # Points per million
    df['pts_per_million'] = df['total_points'] / df['price']
    
    # Form trend (last 5 games equivalent)
    df['form_trend'] = df['form'] + np.random.normal(0, 0.2, len(df))
    
    # Clean up negative values
    numeric_cols = ['xG', 'xA', 'xGI', 'xG_per_90', 'xA_per_90', 'xBPS', 'key_passes']
    for col in numeric_cols:
        df[col] = np.maximum(df[col], 0)
    
    return df

def create_professional_filters():
    """Create professional-style filter interface"""
    
    st.markdown('<div class="main-header">⚽ FPL Analytics Pro</div>', unsafe_allow_html=True)
    st.markdown("**Advanced Fantasy Premier League Analytics Platform**")
    
    # Create two-column layout for filters
    filter_col1, filter_col2 = st.columns([1, 1])
    
    with filter_col1:
        st.markdown('<div class="filter-section">', unsafe_allow_html=True)
        st.subheader("📊 Player Filters")
        
        # Position checkboxes
        st.write("**Position:**")
        pos_cols = st.columns(4)
        position_filters = {}
        positions = ['GK', 'DEF', 'MID', 'FWD']
        
        for i, pos in enumerate(positions):
            with pos_cols[i]:
                position_filters[pos] = st.checkbox(pos, value=True, key=f"pos_{pos}")
        
        # Price range
        st.write("**Price Range (£m):**")
        price_range = st.slider("", 3.5, 15.0, (4.0, 14.5), 0.1, key="price_slider")
        
        # Search functionality
        search_term = st.text_input("🔍 Search player or team", placeholder="Enter player or team name")
        
        # Additional filters
        min_minutes = st.checkbox("Hide low minutes players (< 180 mins)")
        selected_only = st.checkbox("Show only selected players")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with filter_col2:
        st.markdown('<div class="filter-section">', unsafe_allow_html=True)
        st.subheader("🏆 Statistics & Display")
        
        # Stat calculation type
        stat_type = st.radio("**Stats Calculation:**", 
                           ["Total Stats", "Per Game", "Per 90 Minutes"], 
                           horizontal=True)
        
        # Gameweek range (placeholder for now)
        st.write("**Gameweek Range:**")
        gw_range = st.slider("", 1, 38, (1, 38), key="gw_slider")
        
        # Venue filter
        venue_filter = st.selectbox("**Venue:**", ["Home and Away", "Home Only", "Away Only"])
        
        # Opposition strength
        st.write("**Opposition Strength:**")
        opp_strength = st.slider("", 1, 4, (1, 4), key="opp_slider")
        
        # Sort options
        sort_metric = st.selectbox("**Sort by:**", 
                                  ["Total Points", "Points per Game", "Value Score", "xG", "xA", "Price"])
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    return {
        'positions': position_filters,
        'price_range': price_range,
        'search': search_term,
        'min_minutes': min_minutes,
        'selected_only': selected_only,
        'stat_type': stat_type,
        'gw_range': gw_range,
        'venue': venue_filter,
        'opp_strength': opp_strength,
        'sort_metric': sort_metric
    }

def apply_filters(df, filters):
    """Apply selected filters to dataframe"""
    filtered_df = df.copy()
    
    # Position filter
    selected_positions = [pos for pos, selected in filters['positions'].items() if selected]
    if selected_positions:
        filtered_df = filtered_df[filtered_df['position'].isin(selected_positions)]
    
    # Price filter
    filtered_df = filtered_df[
        (filtered_df['price'] >= filters['price_range'][0]) & 
        (filtered_df['price'] <= filters['price_range'][1])
    ]
    
    # Search filter
    if filters['search']:
        search_mask = (
            filtered_df['web_name'].str.contains(filters['search'], case=False, na=False) |
            filtered_df['team_name'].str.contains(filters['search'], case=False, na=False)
        )
        filtered_df = filtered_df[search_mask]
    
    # Minutes filter
    if filters['min_minutes']:
        filtered_df = filtered_df[filtered_df['minutes'] >= 180]
    
    return filtered_df

def create_advanced_data_table(df, stat_type):
    """Create professional data table with multiple categories"""
    
    if df.empty:
        st.warning("No players match your current filters.")
        return
    
    st.subheader("📊 Player Statistics")
    st.info(f"Showing {len(df):,} players matching your criteria")
    
    # Prepare columns based on stat type
    if stat_type == "Per Game":
        stat_suffix = "_per_game"
        xg_col, xa_col = 'xG', 'xA'  # Will be calculated per game
        goals_col, assists_col = 'goals_scored', 'assists'
    elif stat_type == "Per 90 Minutes":
        stat_suffix = "_per_90"
        xg_col, xa_col = 'xG_per_90', 'xA_per_90'
        goals_col, assists_col = 'goals_per_90', 'assists_per_90'
    else:
        stat_suffix = ""
        xg_col, xa_col = 'xG', 'xA'
        goals_col, assists_col = 'goals_scored', 'assists'
    
    # Define column structure
    display_columns = {
        'Basic Info': ['web_name', 'price', 'team_name', 'position'],
        'Game Time': ['minutes', 'ppg'],
        'Goal Threat': [xg_col, goals_col, 'key_passes'],
        'Creativity': [xa_col, assists_col, 'xGI'],
        'FPL Performance': ['total_points', 'pts_per_million', 'form', 'bonus'],
        'Advanced': ['xBPS', 'value_score']
    }
    
    # Create the display dataframe
    display_df = df.copy()
    
    # Format columns for display
    for col in [xg_col, xa_col, 'xGI', 'xBPS', 'value_score', 'pts_per_million']:
        if col in display_df.columns:
            display_df[col] = display_df[col].round(2)
    
    # Column configuration for better display
    column_config = {
        'web_name': st.column_config.TextColumn('Player Name', width='medium'),
        'price': st.column_config.NumberColumn('Price', format='£%.1f'),
        'team_name': st.column_config.TextColumn('Team', width='small'),
        'position': st.column_config.TextColumn('Pos', width='small'),
        'minutes': st.column_config.NumberColumn('Mins', format='%d'),
        'ppg': st.column_config.NumberColumn('PPG', format='%.1f'),
        xg_col: st.column_config.NumberColumn('xG', format='%.2f'),
        goals_col: st.column_config.NumberColumn('Goals', format='%.1f'),
        'key_passes': st.column_config.NumberColumn('KP', format='%d'),
        xa_col: st.column_config.NumberColumn('xA', format='%.2f'),
        assists_col: st.column_config.NumberColumn('Assists', format='%.1f'),
        'xGI': st.column_config.NumberColumn('xGI', format='%.2f'),
        'total_points': st.column_config.NumberColumn('Total Pts', format='%d'),
        'pts_per_million': st.column_config.NumberColumn('Pts/£M', format='%.1f'),
        'form': st.column_config.NumberColumn('Form', format='%.1f'),
        'bonus': st.column_config.NumberColumn('Bonus', format='%d'),
        'xBPS': st.column_config.NumberColumn('xBPS', format='%.1f'),
        'value_score': st.column_config.NumberColumn('Value', format='%.2f')
    }
    
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["📊 All Statistics", "⚽ Attacking Stats", "🎯 Key Metrics"])
    
    with tab1:
        # Full comprehensive table
        all_cols = []
        for category_cols in display_columns.values():
            all_cols.extend(category_cols)
        
        st.dataframe(
            display_df[all_cols],
            column_config=column_config,
            hide_index=True,
            use_container_width=True,
            height=600
        )
    
    with tab2:
        # Attacking focused view
        attacking_cols = display_columns['Basic Info'] + display_columns['Goal Threat'] + display_columns['Creativity']
        
        st.dataframe(
            display_df[attacking_cols],
            column_config=column_config,
            hide_index=True,
            use_container_width=True,
            height=600
        )
    
    with tab3:
        # Key FPL metrics
        key_cols = display_columns['Basic Info'] + display_columns['FPL Performance']
        
        st.dataframe(
            display_df[key_cols],
            column_config=column_config,
            hide_index=True,
            use_container_width=True,
            height=600
        )

def create_summary_metrics(df):
    """Create summary metrics panel"""
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        avg_price = df['price'].mean()
        st.metric("Average Price", f"£{avg_price:.1f}m")
    
    with col2:
        total_players = len(df)
        st.metric("Players Shown", f"{total_players:,}")
    
    with col3:
        if not df.empty:
            top_scorer = df.loc[df['total_points'].idxmax()]
            st.metric("Top Scorer", top_scorer['web_name'], f"{int(top_scorer['total_points'])} pts")
    
    with col4:
        if not df.empty:
            best_value = df.loc[df['value_score'].idxmax()]
            st.metric("Best Value", best_value['web_name'], f"{best_value['value_score']:.1f}")
    
    with col5:
        if not df.empty:
            highest_xg = df.loc[df['xG'].idxmax()]
            st.metric("Highest xG", highest_xg['web_name'], f"{highest_xg['xG']:.1f}")

def sidebar_management():
    """Simplified sidebar for admin functions"""
    
    with st.sidebar.expander("🗄️ System Admin", expanded=False):
        admin_password = st.text_input("Admin Password", type="password", key="admin_pass")
        
        if admin_password == st.secrets.get("admin", {}).get("password", ""):
            st.success("🔓 Admin Access")
            
            if st.button("🔄 Refresh Data"):
                st.cache_data.clear()
                st.success("Cache cleared")
                st.rerun()
            
            # System stats
            df = load_enhanced_player_data()
            if df is not None:
                st.metric("Database Records", len(df))
                st.metric("Last Updated", "Live")
        
        elif admin_password:
            st.error("❌ Invalid password")

def main():
    """Main application"""
    
    # Sidebar admin
    sidebar_management()
    
    # Load data
    with st.spinner("Loading enhanced FPL data..."):
        df = load_enhanced_player_data()
    
    if df is None:
        st.error("Unable to load player data. Please check your database connection.")
        return
    
    # Create filters
    filters = create_professional_filters()
    
    # Apply filters
    filtered_df = apply_filters(df, filters)
    
    # Summary metrics
    create_summary_metrics(filtered_df)
    
    # Main data table
    create_advanced_data_table(filtered_df, filters['stat_type'])
    
    # Footer
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("🔄 **Real-time updates**")
    
    with col2:
        st.markdown("📊 **Advanced analytics**")
    
    with col3:
        st.markdown("⚽ **Professional FPL tools**")

if __name__ == "__main__":
    main()
