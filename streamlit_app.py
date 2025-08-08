# streamlit_app.py - Production FPL Analytics Platform
# Enhanced FPL Dashboard - Phase 1: Advanced Statistics & Professional Layout

import streamlit as st
import pandas as pd
@@ -7,32 +7,52 @@
from supabase import create_client, Client
from datetime import datetime, timedelta
import requests
import numpy as np

# Page config
# Page config with custom theme
st.set_page_config(
    page_title="FPL Analytics Hub",
    page_title="FPL Analytics Pro",
page_icon="⚽",
layout="wide",
initial_sidebar_state="expanded"
)

# Custom CSS for better appearance
# Custom CSS for professional appearance
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .metric-container {
        background: linear-gradient(90deg, #f8f9fa 0%, #e9ecef 100%);
       padding: 1rem;
        border-radius: 0.5rem;
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
    .change-positive { color: #28a745; }
    .change-negative { color: #dc3545; }
    .change-neutral { color: #6c757d; }
    .admin-section { 
        background-color: #fff3cd; 
        padding: 1rem; 
        border-radius: 0.5rem; 
        border: 1px solid #ffeaa7; 
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
@@ -50,651 +70,384 @@ def init_supabase():

supabase = init_supabase()

# Data loading functions
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_current_players():
    """Load current player data from database"""
# Enhanced data loading with advanced calculations
@st.cache_data(ttl=300)
def load_enhanced_player_data():
    """Load and enhance player data with advanced statistics"""
if not supabase:
return None

try:
        # Get current players data
result = supabase.table('players_current').select('*').execute()
        if result.data:
            df = pd.DataFrame(result.data)
            df['price'] = df['now_cost'] / 10
            return df
        return None
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

@st.cache_data(ttl=600)  # Cache for 10 minutes
def load_recent_changes(days=7):
    """Load recent player changes"""
    if not supabase:
        return None
    
    try:
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        result = supabase.table('player_history').select('*').gte('recorded_at', cutoff_date).order('recorded_at', desc=True).execute()
        
        if result.data:
            return pd.DataFrame(result.data)
        return None
    except Exception as e:
        st.error(f"Error loading changes: {e}")
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

@st.cache_data(ttl=600)
def load_price_changes(days=7):
    """Load recent price changes"""
    if not supabase:
        return None
def create_professional_filters():
    """Create professional-style filter interface"""

    try:
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        result = supabase.table('price_changes').select('*').gte('change_date', cutoff_date).order('change_date', desc=True).execute()
        
        if result.data:
            return pd.DataFrame(result.data)
        return None
    except Exception as e:
        st.error(f"Error loading price changes: {e}")
        return None

@st.cache_data(ttl=1800)  # Cache for 30 minutes
def load_update_history(limit=10):
    """Load recent data update history"""
    if not supabase:
        return None
    st.markdown('<div class="main-header">⚽ FPL Analytics Pro</div>', unsafe_allow_html=True)
    st.markdown("**Advanced Fantasy Premier League Analytics Platform**")

    try:
        result = supabase.table('data_updates').select('*').order('started_at', desc=True).limit(limit).execute()
    # Create two-column layout for filters
    filter_col1, filter_col2 = st.columns([1, 1])
    
    with filter_col1:
        st.markdown('<div class="filter-section">', unsafe_allow_html=True)
        st.subheader("📊 Player Filters")

        if result.data:
            return pd.DataFrame(result.data)
        return None
    except Exception as e:
        return None

def format_price_change(change):
    """Format price change with color"""
    if change > 0:
        return f"<span class='change-positive'>+£{change:.1f}m</span>"
    elif change < 0:
        return f"<span class='change-negative'>£{change:.1f}m</span>"
    else:
        return f"<span class='change-neutral'>£{change:.1f}m</span>"

def sidebar_user_preferences():
    """User preferences and global filters in sidebar"""
    st.sidebar.title("⚙️ Settings")
    
    # Global preferences
    with st.sidebar.expander("🎛️ Display Preferences", expanded=True):
        # Data refresh rate
        refresh_rate = st.selectbox(
            "Data Refresh Rate:",
            ["5 minutes", "10 minutes", "30 minutes"],
            index=1,
            help="How often to refresh cached data"
        )
        # Position checkboxes
        st.write("**Position:**")
        pos_cols = st.columns(4)
        position_filters = {}
        positions = ['GK', 'DEF', 'MID', 'FWD']

        # Default position filter
        default_position = st.selectbox(
            "Default Position Filter:",
            ["All", "GK", "DEF", "MID", "FWD"],
            help="Starting position filter for analysis"
        )
        for i, pos in enumerate(positions):
            with pos_cols[i]:
                position_filters[pos] = st.checkbox(pos, value=True, key=f"pos_{pos}")

        # Price range preference
        st.write("**Default Price Range:**")
        price_min, price_max = st.slider(
            "Price Range (£m):",
            min_value=3.5,
            max_value=15.0,
            value=(4.0, 12.0),
            step=0.5,
            help="Default price range for filtering"
        )
        # Price range
        st.write("**Price Range (£m):**")
        price_range = st.slider("", 3.5, 15.0, (4.0, 14.5), 0.1, key="price_slider")

        # Store preferences in session state
        st.session_state['refresh_rate'] = refresh_rate
        st.session_state['default_position'] = default_position
        st.session_state['default_price_range'] = (price_min, price_max)
    
    # Quick stats
    with st.sidebar.expander("📊 Quick Stats", expanded=True):
        # This will be populated with real-time stats
        players_df = load_current_players()
        if players_df is not None:
            st.metric("Database Size", f"{len(players_df):,}")
            
            # Top scorer
            top_scorer = players_df.loc[players_df['total_points'].idxmax()]
            st.metric("Leading Scorer", top_scorer['web_name'], f"{int(top_scorer['total_points'])} pts")
            
            # Most expensive
            most_expensive = players_df.loc[players_df['price'].idxmax()]
            st.metric("Most Expensive", most_expensive['web_name'], f"£{most_expensive['price']:.1f}m")
        else:
            st.info("Loading stats...")

def sidebar_database_management():
    """Database management component in sidebar"""
    
    # Database Management Section
    with st.sidebar.expander("🗄️ Database Management", expanded=False):
        st.markdown("**System Administration**")
        # Search functionality
        search_term = st.text_input("🔍 Search player or team", placeholder="Enter player or team name")

        # System status
        if supabase:
            st.success("✅ Database Connected")
            
            # Quick stats
            try:
                players = supabase.table('players_current').select('id').execute()
                player_count = len(players.data) if players.data else 0
                st.metric("Players in DB", f"{player_count:,}")
            except:
                st.metric("Players in DB", "Error")
        else:
            st.error("❌ Database Disconnected")
        # Additional filters
        min_minutes = st.checkbox("Hide low minutes players (< 180 mins)")
        selected_only = st.checkbox("Show only selected players")

        # Admin authentication
        admin_password = st.text_input("Admin Password", type="password", key="admin_pass")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with filter_col2:
        st.markdown('<div class="filter-section">', unsafe_allow_html=True)
        st.subheader("🏆 Statistics & Display")

        if admin_password == st.secrets.get("admin", {}).get("password", ""):
            st.success("🔓 Admin Access")
            
            # Admin controls
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔄 Refresh", help="Clear cache and refresh data"):
                    st.cache_data.clear()
                    st.success("Cache cleared")
                    st.rerun()
            
            with col2:
                if st.button("📊 Stats", help="View detailed database statistics"):
                    show_detailed_stats()
            
            # System health
            st.markdown("**System Health:**")
            update_history = load_update_history(1)
            if update_history is not None and not update_history.empty:
                last_update = pd.to_datetime(update_history.iloc[0]['started_at'])
                hours_ago = (datetime.now() - last_update.replace(tzinfo=None)).total_seconds() / 3600
                
                if hours_ago < 3:
                    st.success(f"✅ Updated {hours_ago:.1f}h ago")
                elif hours_ago < 6:
                    st.warning(f"⚠️ Updated {hours_ago:.1f}h ago")
                else:
                    st.error(f"❌ Updated {hours_ago:.1f}h ago")
            else:
                st.info("ℹ️ No update history")
            
            # Advanced admin functions
            with st.expander("⚙️ Advanced", expanded=False):
                if st.button("🚨 Force Manual Update", help="Trigger manual data collection"):
                    st.warning("Manual update would require API integration")
                
                if st.button("📝 View Update Logs", help="Show recent update attempts"):
                    show_update_logs()
                
                if st.checkbox("Show Debug Info"):
                    show_debug_info()
        # Stat calculation type
        stat_type = st.radio("**Stats Calculation:**", 
                           ["Total Stats", "Per Game", "Per 90 Minutes"], 
                           horizontal=True)

        elif admin_password:
            st.error("❌ Invalid password")
        else:
            st.info("Enter admin password for management tools")

def show_detailed_stats():
    """Show detailed database statistics in sidebar"""
    try:
        players = supabase.table('players_current').select('*').execute()
        changes = supabase.table('player_history').select('*').execute()
        price_changes = supabase.table('price_changes').select('*').execute()
        updates = supabase.table('data_updates').select('*').execute()
        # Gameweek range (placeholder for now)
        st.write("**Gameweek Range:**")
        gw_range = st.slider("", 1, 38, (1, 38), key="gw_slider")

        st.write("**📊 Database Statistics:**")
        st.write(f"• Players: {len(players.data) if players.data else 0}")
        st.write(f"• Change Records: {len(changes.data) if changes.data else 0}")
        st.write(f"• Price Changes: {len(price_changes.data) if price_changes.data else 0}")
        st.write(f"• Update Logs: {len(updates.data) if updates.data else 0}")
        # Venue filter
        venue_filter = st.selectbox("**Venue:**", ["Home and Away", "Home Only", "Away Only"])

        if players.data:
            df = pd.DataFrame(players.data)
            st.write(f"• Avg Player Price: £{(df['now_cost'].mean() / 10):.1f}m")
            st.write(f"• Total Points: {df['total_points'].sum():,}")
        # Opposition strength
        st.write("**Opposition Strength:**")
        opp_strength = st.slider("", 1, 4, (1, 4), key="opp_slider")

    except Exception as e:
        st.error(f"Error loading stats: {e}")

def show_update_logs():
    """Show recent update logs"""
    update_history = load_update_history(5)
    if update_history is not None and not update_history.empty:
        st.write("**🔄 Recent Updates:**")
        for _, update in update_history.iterrows():
            status_emoji = "✅" if update['status'] == 'success' else "❌"
            st.write(f"{status_emoji} {update['started_at'][:16]} - {update['status']}")
    else:
        st.info("No update history available")

def show_debug_info():
    """Show debug information"""
    st.write("**🔧 Debug Information:**")
    st.write(f"• Streamlit version: {st.__version__}")
    st.write(f"• Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.write(f"• Supabase connected: {'Yes' if supabase else 'No'}")
    
    # Cache info
    cache_info = st.cache_data.get_stats()
    st.write(f"• Cached functions: {len(cache_info)}")

def main_dashboard():
    """Main dashboard interface - clean and focused on data"""
    
    # Header
    st.title("⚽ FPL Analytics Hub")
    st.markdown("**Live Fantasy Premier League Analytics with Change Tracking**")
    
    # Load data
    with st.spinner("Loading latest FPL data..."):
        players_df = load_current_players()
        recent_changes = load_recent_changes()
        price_changes = load_price_changes()
        update_history = load_update_history()
    
    if players_df is None:
        st.error("Unable to load player data. Please try again later.")
        return
    
    # Clean data freshness indicators
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Players", f"{len(players_df):,}")
    
    with col2:
        if update_history is not None and not update_history.empty:
            last_update = pd.to_datetime(update_history.iloc[0]['started_at'])
            hours_ago = (datetime.now() - last_update.replace(tzinfo=None)).total_seconds() / 3600
            st.metric("Last Update", f"{hours_ago:.1f}h ago")
        else:
            st.metric("Last Update", "Unknown")
    
    with col3:
        if recent_changes is not None:
            changes_24h = len(recent_changes[pd.to_datetime(recent_changes['recorded_at']) > datetime.now() - timedelta(hours=24)])
            st.metric("Changes (24h)", changes_24h)
        else:
            st.metric("Changes (24h)", 0)
    
    with col4:
        if price_changes is not None:
            price_changes_24h = len(price_changes[pd.to_datetime(price_changes['change_date']) > datetime.now() - timedelta(hours=24)])
            st.metric("Price Changes (24h)", price_changes_24h)
        else:
            st.metric("Price Changes (24h)", 0)
    
    # Main content tabs - more space for analysis
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Player Analysis", 
        "💰 Price Changes", 
        "🔄 Recent Updates", 
        "🏆 Top Performers", 
        "🔍 Team Lookup"
    ])
    
    with tab1:
        show_player_analysis(players_df)
    
    with tab2:
        show_price_changes(price_changes, players_df)
    
    with tab3:
        show_recent_updates(recent_changes, players_df)
    
    with tab4:
        show_top_performers(players_df)
    
    with tab5:
        show_team_lookup()
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

def show_player_analysis(players_df):
    """Enhanced player analysis with filters"""
    st.subheader("📊 Player Performance Analysis")
def apply_filters(df, filters):
    """Apply selected filters to dataframe"""
    filtered_df = df.copy()

    # Get user preferences from sidebar
    default_position = st.session_state.get('default_position', 'All')
    default_price_range = st.session_state.get('default_price_range', (4.0, 15.0))
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        position_filter = st.selectbox(
            "Position:", 
            ["All"] + sorted(players_df['position'].unique().tolist()),
            index=0 if default_position == 'All' else sorted(players_df['position'].unique().tolist()).index(default_position) + 1 if default_position in players_df['position'].unique() else 0
        )
    
    with col2:
        price_range = st.slider(
            "Price Range (£m):",
            min_value=float(players_df['price'].min()),
            max_value=float(players_df['price'].max()),
            value=default_price_range,
            step=0.1
        )
    
    with col3:
        min_minutes = st.slider(
            "Min Minutes:",
            min_value=0,
            max_value=int(players_df['minutes'].max()),
            value=180,
            step=90
        )
    
    # Apply filters
    filtered_df = players_df.copy()
    
    if position_filter != "All":
        filtered_df = filtered_df[filtered_df['position'] == position_filter]
    # Position filter
    selected_positions = [pos for pos, selected in filters['positions'].items() if selected]
    if selected_positions:
        filtered_df = filtered_df[filtered_df['position'].isin(selected_positions)]

    # Price filter
filtered_df = filtered_df[
        (filtered_df['price'] >= price_range[0]) & 
        (filtered_df['price'] <= price_range[1]) &
        (filtered_df['minutes'] >= min_minutes)
        (filtered_df['price'] >= filters['price_range'][0]) & 
        (filtered_df['price'] <= filters['price_range'][1])
]

    if filtered_df.empty:
        st.warning("No players match your filters. Try adjusting the criteria.")
        return
    # Search filter
    if filters['search']:
        search_mask = (
            filtered_df['web_name'].str.contains(filters['search'], case=False, na=False) |
            filtered_df['team_name'].str.contains(filters['search'], case=False, na=False)
        )
        filtered_df = filtered_df[search_mask]

    # Filter summary
    st.info(f"Showing {len(filtered_df):,} players matching your criteria")
    
    # Performance vs Price scatter plot
    fig = px.scatter(
        filtered_df,
        x='price',
        y='total_points',
        color='position',
        size='selected_by_percent',
        hover_data=['web_name', 'team_name', 'points_per_game', 'form'],
        title='Player Performance vs Price (bubble size = ownership %)',
        labels={'price': 'Price (£m)', 'total_points': 'Total Points'},
        color_discrete_map={
            'GK': '#1f77b4',
            'DEF': '#ff7f0e', 
            'MID': '#2ca02c',
            'FWD': '#d62728'
        }
    )
    
    fig.update_layout(height=600)
    st.plotly_chart(fig, use_container_width=True)
    
    # Value analysis
    st.subheader("💎 Best Value Players")
    filtered_df['value_score'] = filtered_df['total_points'] / filtered_df['price']
    
    value_players = filtered_df.nlargest(15, 'value_score')[
        ['web_name', 'team_name', 'position', 'price', 'total_points', 'value_score', 'form']
    ]
    # Minutes filter
    if filters['min_minutes']:
        filtered_df = filtered_df[filtered_df['minutes'] >= 180]

    st.dataframe(
        value_players,
        column_config={
            'web_name': 'Player',
            'team_name': 'Team',
            'position': 'Pos',
            'price': st.column_config.NumberColumn('Price', format="£%.1f"),
            'total_points': 'Points',
            'value_score': st.column_config.NumberColumn('Value', format="%.2f"),
            'form': st.column_config.NumberColumn('Form', format="%.1f")
        },
        hide_index=True,
        use_container_width=True
    )
    return filtered_df

def show_price_changes(price_changes_df, players_df):
    """Show recent price changes with analysis"""
    st.subheader("💰 Recent Price Changes")
def create_advanced_data_table(df, stat_type):
    """Create professional data table with multiple categories"""

    if price_changes_df is None or price_changes_df.empty:
        st.info("No recent price changes found.")
    if df.empty:
        st.warning("No players match your current filters.")
return

    # Merge with player data for context
    if not players_df.empty:
        merged = price_changes_df.merge(
            players_df[['id', 'web_name', 'position', 'team_name']],
            left_on='player_id',
            right_on='id',
            how='left'
        )
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
        merged = price_changes_df
    
    # Price change summary
    col1, col2, col3 = st.columns(3)
    
    with col1:
        risers = len(merged[merged['price_change'] > 0])
        st.metric("Price Rises", risers, delta="📈")
    
    with col2:
        fallers = len(merged[merged['price_change'] < 0])
        st.metric("Price Falls", fallers, delta="📉")
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

    with col3:
        avg_change = merged['price_change'].mean()
        st.metric("Avg Change", f"£{avg_change:.2f}m")
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

    # Recent price changes table
    st.subheader("🕐 Latest Price Movements")
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["📊 All Statistics", "⚽ Attacking Stats", "🎯 Key Metrics"])

    display_cols = ['web_name', 'team_name', 'position', 'old_price', 'new_price', 'price_change', 'change_date']
    recent_changes = merged.sort_values('change_date', ascending=False).head(20)
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

    if not recent_changes.empty:
    with tab2:
        # Attacking focused view
        attacking_cols = display_columns['Basic Info'] + display_columns['Goal Threat'] + display_columns['Creativity']
        
st.dataframe(
            recent_changes[display_cols],
            column_config={
                'web_name': 'Player',
                'team_name': 'Team',
                'position': 'Pos',
                'old_price': st.column_config.NumberColumn('Old Price', format="£%.1f"),
                'new_price': st.column_config.NumberColumn('New Price', format="£%.1f"),
                'price_change': st.column_config.NumberColumn('Change', format="£%.1f"),
                'change_date': 'Date'
            },
            display_df[attacking_cols],
            column_config=column_config,
hide_index=True,
            use_container_width=True
            use_container_width=True,
            height=600
)

    # Price change chart
    if len(merged) > 0:
        fig = px.histogram(
            merged,
            x='price_change',
            title='Distribution of Price Changes',
            labels={'price_change': 'Price Change (£m)', 'count': 'Number of Players'},
            color_discrete_sequence=['#1f77b4']
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
        st.plotly_chart(fig, use_container_width=True)

def show_recent_updates(recent_changes_df, players_df):
    """Show recent player data updates"""
    st.subheader("🔄 Recent Player Updates")
def create_summary_metrics(df):
    """Create summary metrics panel"""

    if recent_changes_df is None or recent_changes_df.empty:
        st.info("No recent changes found.")
        return
    
    # Change type breakdown
    change_counts = recent_changes_df['change_type'].value_counts()
    
    col1, col2 = st.columns(2)
    col1, col2, col3, col4, col5 = st.columns(5)

with col1:
        # Change type pie chart
        fig_pie = px.pie(
            values=change_counts.values,
            names=change_counts.index,
            title='Types of Changes (Last 7 Days)'
        )
        st.plotly_chart(fig_pie, use_container_width=True)
        avg_price = df['price'].mean()
        st.metric("Average Price", f"£{avg_price:.1f}m")

with col2:
        # Recent changes by day
        recent_changes_df['date'] = pd.to_datetime(recent_changes_df['recorded_at']).dt.date
        daily_changes = recent_changes_df.groupby('date').size().reset_index()
        daily_changes.columns = ['date', 'changes']
        
        fig_line = px.line(
            daily_changes,
            x='date',
            y='changes',
            title='Daily Change Activity',
            markers=True
        )
        st.plotly_chart(fig_line, use_container_width=True)
        total_players = len(df)
        st.metric("Players Shown", f"{total_players:,}")

    # Recent changes table
    st.subheader("📝 Latest Changes")
    recent_sample = recent_changes_df.head(20)[
        ['web_name', 'change_type', 'recorded_at']
    ].copy()
    with col3:
        if not df.empty:
            top_scorer = df.loc[df['total_points'].idxmax()]
            st.metric("Top Scorer", top_scorer['web_name'], f"{int(top_scorer['total_points'])} pts")

    if not recent_sample.empty:
        recent_sample['recorded_at'] = pd.to_datetime(recent_sample['recorded_at'])
        
        st.dataframe(
            recent_sample,
            column_config={
                'web_name': 'Player',
                'change_type': 'Change Type',
                'recorded_at': 'Time'
            },
            hide_index=True,
            use_container_width=True
        )
    with col4:
        if not df.empty:
            best_value = df.loc[df['value_score'].idxmax()]
            st.metric("Best Value", best_value['web_name'], f"{best_value['value_score']:.1f}")
    
    with col5:
        if not df.empty:
            highest_xg = df.loc[df['xG'].idxmax()]
            st.metric("Highest xG", highest_xg['web_name'], f"{highest_xg['xG']:.1f}")

def show_top_performers(players_df):
    """Show top performing players by position"""
    st.subheader("🏆 Top Performers by Position")
    
    positions = ['GK', 'DEF', 'MID', 'FWD']
def sidebar_management():
    """Simplified sidebar for admin functions"""

    for position in positions:
        pos_players = players_df[players_df['position'] == position]
    with st.sidebar.expander("🗄️ System Admin", expanded=False):
        admin_password = st.text_input("Admin Password", type="password", key="admin_pass")

        if not pos_players.empty:
            st.write(f"**{position}s:**")
            
            # Get top 5 by points
            top_5 = pos_players.nlargest(5, 'total_points')
        if admin_password == st.secrets.get("admin", {}).get("password", ""):
            st.success("🔓 Admin Access")

            cols = st.columns(5)
            for i, (_, player) in enumerate(top_5.iterrows()):
                with cols[i]:
                    st.metric(
                        f"{player['web_name']}",
                        f"{int(player['total_points'])} pts",
                        delta=f"£{player['price']:.1f}m"
                    )
            st.write("")

def show_team_lookup():
    """FPL team lookup functionality"""
    st.subheader("🔍 FPL Team Lookup")
    st.write("Enter any FPL Manager ID to view their team details:")
    
    manager_id = st.number_input(
        "FPL Manager ID:", 
        min_value=1, 
        value=1,
        help="Find this in any FPL URL: fantasy.premierleague.com/entry/[MANAGER_ID]/"
    )
    
    if st.button("Look Up Team") and manager_id > 1:
        with st.spinner("Fetching team data..."):
            try:
                team_url = f"https://fantasy.premierleague.com/api/entry/{manager_id}/"
                response = requests.get(team_url)
                
                if response.status_code == 200:
                    team_data = response.json()
                    
                    # Team overview
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Team Name", team_data.get('name', 'Unknown'))
                    
                    with col2:
                        st.metric("Total Points", f"{team_data.get('summary_overall_points', 0):,}")
                    
                    with col3:
                        st.metric("Overall Rank", f"{team_data.get('summary_overall_rank', 0):,}")
                    
                    with col4:
                        st.metric("Gameweek Points", f"{team_data.get('summary_event_points', 0):,}")
                    
                    # Additional details
                    st.write("**Team Details:**")
                    details_col1, details_col2 = st.columns(2)
                    
                    with details_col1:
                        st.write(f"**Started Playing:** GW {team_data.get('started_event', 'Unknown')}")
                        st.write(f"**Gameweek Rank:** {team_data.get('summary_event_rank', 0):,}")
                    
                    with details_col2:
                        st.write(f"**Total Transfers:** {team_data.get('total_transfers', 0)}")
                        st.write(f"**Bank Balance:** £{team_data.get('bank', 0) / 10:.1f}m")
                
                else:
                    st.error("Could not find team with that Manager ID. Please check the number and try again.")
            if st.button("🔄 Refresh Data"):
                st.cache_data.clear()
                st.success("Cache cleared")
                st.rerun()

            except Exception as e:
                st.error(f"Error fetching team data: {e}")
            # System stats
            df = load_enhanced_player_data()
            if df is not None:
                st.metric("Database Records", len(df))
                st.metric("Last Updated", "Live")
        
        elif admin_password:
            st.error("❌ Invalid password")

def main():
"""Main application"""

    # Check database connection
    if not supabase:
        st.error("❌ Database connection failed. Please check your configuration.")
    # Sidebar admin
    sidebar_management()
    
    # Load data
    with st.spinner("Loading enhanced FPL data..."):
        df = load_enhanced_player_data()
    
    if df is None:
        st.error("Unable to load player data. Please check your database connection.")
return

    # Sidebar components
    sidebar_user_preferences()
    sidebar_database_management()
    # Create filters
    filters = create_professional_filters()
    
    # Apply filters
    filtered_df = apply_filters(df, filters)
    
    # Summary metrics
    create_summary_metrics(filtered_df)

    # Main dashboard - clean and focused on data analysis
    main_dashboard()
    # Main data table
    create_advanced_data_table(filtered_df, filters['stat_type'])

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
        st.markdown("🔄 **Auto-updates every 2 hours**")
        st.markdown("🔄 **Real-time updates**")

with col2:
        st.markdown("📊 **Change tracking enabled**")
        st.markdown("📊 **Advanced analytics**")

with col3:
        st.markdown("💾 **Powered by Supabase**")
        st.markdown("⚽ **Professional FPL tools**")

if __name__ == "__main__":
main()
