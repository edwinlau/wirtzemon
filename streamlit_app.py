import streamlit as st
import pandas as pd
import requests

# Page setup
st.set_page_config(page_title="FPL Analytics", page_icon="⚽", layout="wide")

# Title
st.title("⚽ FPL Analytics Dashboard")
st.markdown("**Live Fantasy Premier League Data**")

# Cache data for 30 minutes
@st.cache_data(ttl=1800)
def get_fpl_data():
    """Get FPL data from official API"""
    try:
        url = "https://fantasy.premierleague.com/api/bootstrap-static/"
        response = requests.get(url)
        data = response.json()
        
        # Get player data
        players = data['elements']
        teams = data['teams']
        positions = data['element_types']
        
        # Create lookup dictionaries
        team_names = {team['id']: team['name'] for team in teams}
        position_names = {pos['id']: pos['singular_name_short'] for pos in positions}
        
        # Convert to DataFrame
        df = pd.DataFrame(players)
        df['team_name'] = df['team'].map(team_names)
        df['position'] = df['element_type'].map(position_names)
        df['price'] = df['now_cost'] / 10
        
        return df
    
    except Exception as e:
        st.error(f"Error loading FPL data: {e}")
        return None

# Load data
with st.spinner("Loading FPL data..."):
    df = get_fpl_data()

if df is None:
    st.stop()

# Sidebar filters
st.sidebar.header("Filters")
position_filter = st.sidebar.selectbox("Position:", ["All"] + list(df['position'].unique()))

# Apply filter
if position_filter != "All":
    df = df[df['position'] == position_filter]

# Key stats
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Players", len(df))

with col2:
    avg_price = df['price'].mean()
    st.metric("Average Price", f"£{avg_price:.1f}m")

with col3:
    top_scorer = df.loc[df['total_points'].idxmax()]
    st.metric("Top Scorer", top_scorer['web_name'], f"{top_scorer['total_points']} pts")

# Top players table
st.subheader("🏆 Top Players")

top_players = df.nlargest(20, 'total_points')[
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

df['value'] = df['total_points'] / df['price']
best_value = df.nlargest(15, 'value')[
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
st.markdown("🔄 Data updates every 30 minutes | 📊 Built with Streamlit")
