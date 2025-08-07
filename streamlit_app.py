import streamlit as st
import pandas as pd
import requests
from supabase import create_client, Client
from datetime import datetime
import time

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
st.title("⚽ FPL Analytics Hub")
st.markdown("**Live Fantasy Premier League Data with Database Storage**")

# Show database connection status
if supabase:
    st.success("✅ Connected to Wirtzemon Database")
    
    # Show current database count
    try:
        db_count = supabase.table('players').select('id').execute()
        st.info(f"📊 Current players in database: {len(db_count.data)}")
    except:
        st.info("📊 Checking database...")
else:
    st.error("❌ Database connection failed")
    st.stop()

# Fetch FPL data
@st.cache_data(ttl=1800)
def fetch_fpl_data():
    """Fetch FPL data from official API"""
    try:
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
        
        return df
    except Exception as e:
        st.error(f"Error fetching FPL data: {e}")
        return None

# Store all players function
def store_all_players(df):
    """Store all FPL players in database with progress tracking"""
    
    if df is None or len(df) == 0:
        st.error("No data to store")
        return False
    
    # Create progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Prepare all player data
        players_data = []
        total_players = len(df)
        
        status_text.text("Preparing player data...")
        
        for i, (_, row) in enumerate(df.iterrows()):
            player_data = {
                'id': int(row['id']),
                'web_name': str(row['web_name']),
                'position': str(row['position']),
                'team_name': str(row['team_name']),
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
            }
            players_data.append(player_data)
            
            # Update progress
            progress = (i + 1) / total_players
            progress_bar.progress(progress)
            status_text.text(f"Preparing player {i+1}/{total_players}: {row['web_name']}")
        
        # Store in database
        status_text.text("Storing in database...")
        result = supabase.table('players').upsert(players_data).execute()
        
        progress_bar.progress(1.0)
        status_text.text("✅ Complete!")
        
        st.success(f"🎉 Successfully stored {len(players_data)} players in database!")
        return True
        
    except Exception as e:
        st.error(f"❌ Error storing players: {str(e)}")
        status_text.text("❌ Storage failed")
        return False

# Load FPL data
with st.spinner("Loading FPL data..."):
    df = fetch_fpl_data()

if df is None:
    st.error("Could not load FPL data")
    st.stop()

st.success(f"✅ Loaded {len(df)} players from FPL API")

# Database Management Section
st.subheader("🗄️ Database Management")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📥 Store ALL Players in Database", type="primary"):
        st.write("**Storing all FPL players in database...**")
        success = store_all_players(df)
        
        if success:
            # Refresh database count
            try:
                db_count = supabase.table('players').select('id').execute()
                st.balloons()
                st.success(f"🎉 Database now contains {len(db_count.data)} players!")
            except:
                st.success("🎉 All players stored successfully!")

with col2:
    if st.button("🔍 Check Database Count"):
        try:
            db_count = supabase.table('players').select('id').execute()
            st.metric("Database Records", len(db_count.data))
        except Exception as e:
            st.error(f"Error checking database: {e}")

with col3:
    if st.button("🧹 Clear Database"):
        if st.checkbox("I'm sure I want to delete all players"):
            try:
                supabase.table('players').delete().neq('id', 0).execute()
                st.success("✅ Database cleared")
            except Exception as e:
                st.error(f"Error clearing database: {e}")

# Show sample of database contents
st.subheader("📊 Current Database Contents")
try:
    db_sample = supabase.table('players').select('*').limit(10).execute()
    if db_sample.data:
        st.dataframe(pd.DataFrame(db_sample.data))
    else:
        st.info("Database is empty. Click 'Store ALL Players' to populate it.")
except Exception as e:
    st.error(f"Could not load database sample: {e}")

# Regular dashboard
st.subheader("🏆 Top Performers (Live FPL Data)")

# Sidebar filters
st.sidebar.header("🔍 Filters")
position_filter = st.sidebar.selectbox("Position:", ["All"] + list(df['position'].unique()))

# Apply filter
filtered_df = df.copy()
if position_filter != "All":
    filtered_df = filtered_df[filtered_df['position'] == position_filter]

# Key stats
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Players Shown", len(filtered_df))

with col2:
    avg_price = filtered_df['price'].mean()
    st.metric("Average Price", f"£{avg_price:.1f}m")

with col3:
    top_scorer = filtered_df.loc[filtered_df['total_points'].idxmax()]
    st.metric("Top Scorer", top_scorer['web_name'], f"{top_scorer['total_points']} pts")

# Top players table
top_players = filtered_df.nlargest(20, 'total_points')[
    ['web_name', 'team_name', 'position', 'price', 'total_points', 'points_per_game']
]

st.dataframe(
    top_players,
    column_config={
        'web_name': 'Player',
        'team_name': 'Team', 
        'position': 'Position',
        'price': st.column_config.NumberColumn('Price', format="£%.1f"),
        'total_points': 'Total Points',
        'points_per_game': st.column_config.NumberColumn('PPG', format="%.1f")
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
        'price': st.column_config.NumberColumn('Price', format="£%.1f"),
        'total_points': 'Total Points',
        'value': st.column_config.NumberColumn('Value', format="%.2f")
    },
    hide_index=True,
    use_container_width=True
)

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
st.markdown("🔄 Live FPL data | 💾 Stored in Wirtzemon Database | 📊 Built with Streamlit")
