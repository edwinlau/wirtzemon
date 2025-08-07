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
st.title("⚽ FPL Analytics Dashboard - DEBUG MODE")
st.markdown("**Live Fantasy Premier League Data with Database Storage**")

# Show database connection status
if supabase:
    st.success("✅ Connected to Wirtzemon Database")
else:
    st.error("❌ Database connection failed")
    st.stop()

# Test database connection
def test_database():
    """Test basic database operations"""
    st.subheader("🔍 Database Connection Test")
    
    try:
        # Test simple query
        result = supabase.table('players').select('id').limit(1).execute()
        st.success(f"✅ Database query successful. Current records: {len(result.data)}")
        return True
    except Exception as e:
        st.error(f"❌ Database query failed: {str(e)}")
        st.write("**Full error details:**")
        st.code(str(e))
        return False

# Run database test
db_test_passed = test_database()

if not db_test_passed:
    st.error("Database test failed. Cannot proceed with data storage.")
    st.info("Please check your Supabase table structure and permissions.")

# Simple data fetch (without storage first)
@st.cache_data(ttl=1800)
def fetch_fpl_data_only():
    """Just fetch FPL data without storing"""
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

# Manual database storage test
def store_single_player_test():
    """Test storing just one player"""
    st.subheader("🧪 Single Player Storage Test")
    
    if st.button("Test Store One Player"):
        try:
            # Create a simple test record
            test_player = {
                'id': 1,
                'web_name': 'Test Player',
                'position': 'MID',
                'team_name': 'Test Team',
                'now_cost': 50,
                'total_points': 100,
                'points_per_game': 5.0,
                'selected_by_percent': 10.5,
                'form': 3.0,
                'minutes': 900,
                'goals_scored': 5,
                'assists': 3,
                'clean_sheets': 0,
                'updated_at': datetime.now().isoformat()
            }
            
            st.write("**Attempting to store:**")
            st.json(test_player)
            
            # Try to insert
            result = supabase.table('players').upsert([test_player]).execute()
            
            st.success("✅ Single player stored successfully!")
            st.write("**Database response:**")
            st.json(result.data if hasattr(result, 'data') else str(result))
            
        except Exception as e:
            st.error(f"❌ Single player storage failed: {str(e)}")
            st.write("**Full error details:**")
            st.code(str(e))

# Load FPL data
st.subheader("📡 FPL Data")
with st.spinner("Loading FPL data..."):
    df = fetch_fpl_data_only()

if df is None:
    st.error("Could not load FPL data")
    st.stop()

st.success(f"✅ Loaded {len(df)} players from FPL API")

# Show sample data
st.subheader("📊 Sample FPL Data")
st.write("**First 3 players:**")
sample_data = df.head(3)[['id', 'web_name', 'position', 'team_name', 'price', 'total_points']]
st.dataframe(sample_data)

# Manual storage test
store_single_player_test()

# Batch storage test
def store_batch_test():
    """Test storing multiple players"""
    st.subheader("📦 Batch Storage Test")
    
    if st.button("Test Store 5 Players"):
        try:
            # Take first 5 players
            test_players = []
            for i in range(5):
                row = df.iloc[i]
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
                test_players.append(player_data)
            
            st.write("**Attempting to store 5 players:**")
            st.json(test_players[0])  # Show first player as example
            st.write("... and 4 more players")
            
            # Try batch insert
            result = supabase.table('players').upsert(test_players).execute()
            
            st.success("✅ Batch storage successful!")
            st.write(f"**Stored {len(test_players)} players**")
            
            # Check database
            db_count = supabase.table('players').select('id').execute()
            st.info(f"📊 Total players now in database: {len(db_count.data)}")
            
        except Exception as e:
            st.error(f"❌ Batch storage failed: {str(e)}")
            st.write("**Full error details:**")
            st.code(str(e))

store_batch_test()

# Database inspection
st.subheader("🔍 Database Inspection")

if st.button("Show Database Contents"):
    try:
        result = supabase.table('players').select('*').limit(10).execute()
        if result.data:
            st.success(f"✅ Found {len(result.data)} players in database")
            st.dataframe(pd.DataFrame(result.data))
        else:
            st.warning("⚠️ Database is empty")
    except Exception as e:
        st.error(f"❌ Could not read database: {str(e)}")

# Clear database button
st.subheader("🧹 Database Management")
if st.button("Clear All Players (Reset Database)"):
    try:
        result = supabase.table('players').delete().neq('id', 0).execute()
        st.success("✅ Database cleared")
    except Exception as e:
        st.error(f"❌ Could not clear database: {str(e)}")

# Show basic dashboard
st.subheader("🏆 Top Players (from API)")
top_players = df.nlargest(10, 'total_points')[
    ['web_name', 'team_name', 'position', 'price', 'total_points']
]

st.dataframe(
    top_players,
    column_config={
        'web_name': 'Player',
        'team_name': 'Team', 
        'position': 'Position',
        'price': 'Price (£m)',
        'total_points': 'Total Points'
    },
    hide_index=True,
    use_container_width=True
)
