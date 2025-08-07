import streamlit as st
import pandas as pd
import requests
from supabase import create_client, Client
from datetime import datetime

# Page setup
st.set_page_config(page_title="FPL Analytics", page_icon="⚽", layout="wide")

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

# Title
st.title("⚽ FPL Analytics Dashboard")
st.markdown("**Live Fantasy Premier League Data with Database Storage**")

# Show database connection status
if supabase:
    st.success("✅ Connected to Wirtzemon Database")
else:
    st.error("❌ Database connection failed")

# Cache data for 30 minutes
@st.cache_data(ttl=1800)
def fetch_and_store_fpl_data():
    """Get FPL data and store in Supabase"""
    try:
        # Fetch from FPL API
        url = "https://fantasy.premierleague.com/api/bootstrap-static/"
        response = requests.get(url)
        data = response.json()
        
        # Process data
        players = data['elements']
        teams = data['teams']
        positions = data['element_types']
        
        # Create lookups
        team_names = {team['id']: team['name'] for team in teams}
        position_names = {pos['id']: pos['singular_name_short'] for pos in positions}
        
        # Convert to DataFrame
        df = pd.DataFrame(players)
        df['team_name'] = df['team'].map(team_names)
        df['position'] = df['element_type'].map(position_names)
        df['price'] = df['now_cost'] / 10
        
        # Store in Supabase if connection available
        if supabase:
            st.info("💾 Storing data in database...")
            
            # Prepare data for database
            players_data = []
            for _, row in df.iterrows():
                players_data.append({
                    'id': int(row['id']),
                    'web_name': row['web_name'],
                    'position': row['position'],
                    'team_name': row['team_name'],
                    'now_cost': int(row['now_cost']),
                    'total_points': int(row['total_points']),
                    'points_per_game': float(row['points_per_game']) if pd.notna(row['points_per_game']) else 0.0,
                    'selected_by_percent': float(row['selected_by_percent']),
                    'form': float(row['form']) if pd.notna(row['form']) else 0.0,
                    'minutes': int(row['minutes']),
                    'goals_scored': int(row['goals_scored']),
                    'assists': int(row['assists']),
                    'clean_sheets': int(row['clean_sheets']),
                    'updated_at': datetime.now().isoformat()
                })
            
            # Store in database (upsert to avoid duplicates)
            try:
                result = supabase.table('players').upsert(players_data).execute()
                st.success(f"✅ Stored {len(players_data)} players in database!")
                
                # Show database stats
                db_count = supabase.table('players').select('id').execute()
                st.info(f"📊 Total players in database: {len(db_count.data)}")
                
            except Exception as e:
                st.error(f"Database storage failed: {e}")
        
        return df
    
    except Exception as e:
        st.error(f"Error loading FPL data: {e}")
        return None

@st.cache_data(ttl=600)  # Cache for 10 minutes
def load_from_database():
    """Load player data from Supabase"""
    if not supabase:
        return None
        
    try:
        response = supabase.table('players').select('*').execute()
        if response.data:
            df = pd.DataFrame(response.data)
            df['price'] = df['now_cost'] / 10
            st.info(f"📊 Loaded {len(df)} players from database")
            return df
    except Exception as e:
        st.error(f"Database query failed: {e}")
    
    return None

# Data loading strategy
st.subheader("📡 Data Source")
data_source = st.radio(
    "Choose data source:",
    ["Live API (and store in database)", "Load from database only"],
    help="Live API fetches fresh data. Database loads stored data faster."
)

# Load data based on choice
with st.spinner("Loading FPL data..."):
    if data_source == "Live API (and store in database)":
        df = fetch_and_store_fpl_data()
    else:
        df = load_from_database()
        if df is None:
            st.warning("No data in database. Falling back to live API...")
            df = fetch_and_store_fpl_data()

if df is None:
    st.error("Could not load data from any source")
    st.stop()

# Show data freshness
if 'updated_at' in df.columns:
    latest_update = df['updated_at'].max()
    st.info(f"🕐 Data last updated: {latest_update}")

# Sidebar filters
st.sidebar.header("Filters")
position_filter = st.sidebar.selectbox("Position:", ["All"] + list(df['position'].unique()))

# Apply filter
filtered_df = df.copy()
if position_filter != "All":
    filtered_df = filtered_df[filtered_df['position'] == position_filter]

# Key stats
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Players Shown", len(filtered_df))

with col2:
    avg_price = filtered_df['price'].mean()
    st.metric("Average Price", f"£{avg_price:.1f}m")

with col3:
    top_scorer = filtered_df.loc[filtered_df['total_points'].idxmax()]
    st.metric("Top Scorer", top_scorer['web_name'], f"{top_scorer['total_points']} pts")

with col4:
    if supabase:
        try:
            db_count = supabase.table('players').select('id').execute()
            st.metric("Database Records", len(db_count.data))
        except:
            st.metric("Database Records", "Error")

# Top players table
st.subheader("🏆 Top Players")

top_players = filtered_df.nlargest(20, 'total_points')[
    ['web_name', 'team_name', 'position', 'price', 'total_points', 'points_per_game']
]

st.dataframe(
    top_players,
    column_config={
        'web_name': 'Player',
        'team_name': 'Team', 
        'position': 'Position',
        'price': 'Price (£m)',
        'total_points': 'Total Points',
        'points_per_game': 'Points per Game'
    },
    hide_index=True,
    use_container_width=True
)

# Value analysis
st.subheader("💰 Best Value Players")

filtered_df['value'] = filtered_df['total_points'] / filtered_df['price']
best_value = filtered_df.nlargest(15, 'value')[
    ['web_name', 'team_name', 'position', 'price', 'total_points', 'value']
]

st.dataframe(
    best_value,
    column_config={
        'web_name': 'Player',
        'team_name': 'Team',
        'position': 'Position', 
        'price': 'Price (£m)',
        'total_points': 'Total Points',
        'value': 'Value Score'
    },
    hide_index=True,
    use_container_width=True
)

# Database management
if supabase:
    st.subheader("🗄️ Database Management")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Force Refresh Data"):
            st.cache_data.clear()
            st.rerun()
    
    with col2:
        if st.button("📊 View Database Stats"):
            try:
                # Get table info
                players_count = supabase.table('players').select('id').execute()
                st.write(f"**Players in database:** {len(players_count.data)}")
                
                # Get latest update
                latest = supabase.table('players').select('updated_at').order('updated_at', desc=True).limit(1).execute()
                if latest.data:
                    st.write(f"**Latest update:** {latest.data[0]['updated_at']}")
                
            except Exception as e:
                st.error(f"Error getting database stats: {e}")
    
    with col3:
        if st.button("🧹 Clear Cache"):
            st.cache_data.clear()
            st.success("Cache cleared!")

# Team lookup
st.subheader("🔍 Team Lookup")
manager_id = st.number_input("Enter FPL Manager ID:", min_value=1, value=1)

if st.button("Look Up Team") and manager_id > 1:
    try:
        team_url = f"https://fantasy.premierleague.com/api/entry/{manager_id}/"
        response = requests.get(team_url)
        
        if response.status_code == 200:
            team_data = response.json()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Team Name", team_data['name'])
            with col2:
                st.metric("Total Points", f"{team_data['summary_overall_points']:,}")
            with col3:
                st.metric("Overall Rank", f"{team_data['summary_overall_rank']:,}")
        else:
            st.error("Team not found. Check your Manager ID.")
    
    except Exception as e:
        st.error(f"Error: {e}")

# Footer
st.markdown("---")
st.markdown("🔄 Data updates every 30 minutes | 💾 Stored in Wirtzemon Database | 📊 Built with Streamlit")
