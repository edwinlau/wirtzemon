# streamlit_app.py - Your complete FPL analytics web app

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from supabase import create_client, Client
import os
from datetime import datetime
import time

# Page config
st.set_page_config(
    page_title="FPL Analytics Hub",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Supabase
@st.cache_resource
def init_supabase():
    try:
        SUPABASE_URL = st.secrets["supabase"]["url"]
        SUPABASE_KEY = st.secrets["supabase"]["key"]
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.error(f"Failed to connect to database: {e}")
        return None

supabase = init_supabase()

# Authentication functions
def login():
    st.sidebar.header("🔐 Login")
    
    with st.sidebar.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted and supabase:
            try:
                response = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })
                st.success("Logged in successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Login failed: {str(e)}")

def signup():
    st.sidebar.header("📝 Sign Up")
    
    with st.sidebar.form("signup_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        submitted = st.form_submit_button("Sign Up")
        
        if submitted and supabase:
            if password != confirm_password:
                st.error("Passwords don't match!")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters!")
            else:
                try:
                    response = supabase.auth.sign_up({
                        "email": email,
                        "password": password
                    })
                    st.success("Account created! Please check your email for verification.")
                except Exception as e:
                    st.error(f"Sign up failed: {str(e)}")

def logout():
    if supabase:
        supabase.auth.sign_out()
        if 'user' in st.session_state:
            del st.session_state.user
        st.success("Logged out successfully!")
        st.rerun()

# Data fetching and processing
@st.cache_data(ttl=1800)  # Cache for 30 minutes
def fetch_fpl_data():
    """Fetch FPL data from official API"""
    url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        # Process player data
        players = data['elements']
        teams = data['teams']
        positions = data['element_types']
        
        # Create lookups
        team_lookup = {team['id']: team['name'] for team in teams}
        position_lookup = {pos['id']: pos['singular_name_short'] for pos in positions}
        
        # Convert to DataFrame
        df = pd.DataFrame(players)
        df['team_name'] = df['team'].map(team_lookup)
        df['position'] = df['element_type'].map(position_lookup)
        df['price'] = df['now_cost'] / 10
        df['ownership_pct'] = pd.to_numeric(df['selected_by_percent'])
        
        return df
    except Exception as e:
        st.error(f"Error fetching FPL data: {e}")
        return None

def store_players_in_db(df):
    """Store player data in Supabase"""
    if not supabase or df is None:
        return False
    
    try:
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
        
        # Batch upsert to Supabase
        supabase.table('players').upsert(players_data).execute()
        return True
    except Exception as e:
        st.error(f"Error storing data: {e}")
        return False

@st.cache_data(ttl=600)  # Cache for 10 minutes
def get_players_from_db():
    """Get player data from Supabase database"""
    if not supabase:
        return None
        
    try:
        response = supabase.table('players').select('*').execute()
        if response.data:
            df = pd.DataFrame(response.data)
            df['price'] = df['now_cost'] / 10
            df['ownership_pct'] = df['selected_by_percent']
            return df
        return None
    except Exception as e:
        st.error(f"Error loading data from database: {e}")
        return None

def save_user_team(manager_id, team_name):
    """Save user's FPL team details to database"""
    if not supabase or 'user' not in st.session_state:
        return False
        
    try:
        supabase.table('user_teams').upsert({
            'user_id': st.session_state.user.user.id,
            'manager_id': manager_id,
            'team_name': team_name,
            'updated_at': datetime.now().isoformat()
        }).execute()
        return True
    except Exception as e:
        st.error(f"Error saving team: {e}")
        return False

def get_user_team():
    """Get user's saved team details"""
    if not supabase or 'user' not in st.session_state:
        return None
        
    try:
        response = supabase.table('user_teams').select('*').eq(
            'user_id', st.session_state.user.user.id
        ).execute()
        
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        st.error(f"Error loading user team: {e}")
        return None

# Main app
def main():
    st.title("⚽ FPL Analytics Hub")
    st.markdown("**Your complete Fantasy Premier League analytics platform**")
    
    # Check if database connection exists
    if not supabase:
        st.error("Database connection failed. Please check your configuration.")
        return
    
    # Check authentication
    try:
        user = supabase.auth.get_user()
        if user.user:
            st.session_state.user = user
    except:
        user = None
    
    if not hasattr(st.session_state, 'user') or not st.session_state.get('user'):
        # Not logged in - show login/signup and public dashboard
        tab1, tab2 = st.sidebar.tabs(["Login", "Sign Up"])
        
        with tab1:
            login()
        
        with tab2:
            signup()
        
        # Show public dashboard
        st.info("👆 Login or sign up in the sidebar to access personal features!")
        show_public_dashboard()
    
    else:
        # Logged in - show full dashboard
        st.sidebar.success(f"Welcome!")
        
        if st.sidebar.button("Logout"):
            logout()
        
        # Show full authenticated dashboard
        show_authenticated_dashboard()

def show_public_dashboard():
    """Public dashboard for non-authenticated users"""
    
    # Load data
    with st.spinner("Loading FPL data..."):
        df = fetch_fpl_data()
        
        # Try to store in database if possible
        if df is not None:
            store_players_in_db(df)
        else:
            # Try to load from database as fallback
            df = get_players_from_db()
    
    if df is None:
        st.error("Could not load FPL data. Please try again later.")
        return
    
    # Basic filters
    st.sidebar.header("🔍 Filters")
    position_filter = st.sidebar.selectbox(
        "Position:", 
        ["All"] + sorted(df['position'].unique().tolist())
    )
    
    # Apply filters
    filtered_df = df.copy()
    if position_filter != "All":
        filtered_df = filtered_df[filtered_df['position'] == position_filter]
    
    # Key metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Players", len(filtered_df))
    
    with col2:
        if not filtered_df.empty:
            avg_price = filtered_df['price'].mean()
            st.metric("Average Price", f"£{avg_price:.1f}m")
    
    with col3:
        if not filtered_df.empty:
            top_scorer = filtered_df.loc[filtered_df['total_points'].idxmax()]
            st.metric("Top Scorer", f"{top_scorer['web_name']}", f"{int(top_scorer['total_points'])} pts")
    
    # Top players table
    st.subheader("🏆 Top Performers")
    
    if not filtered_df.empty:
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

def show_authenticated_dashboard():
    """Full dashboard for authenticated users"""
    
    # Navigation tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "👤 My Team", "🔄 Transfers", "📈 Analytics"])
    
    # Load data
    with st.spinner("Loading latest FPL data..."):
        df = fetch_fpl_data()
        if df is not None:
            store_players_in_db(df)
        else:
            df = get_players_from_db()
    
    if df is None:
        st.error("Could not load FPL data.")
        return
    
    with tab1:
        show_main_dashboard(df)
    
    with tab2:
        show_my_team_section(df)
    
    with tab3:
        show_transfer_section(df)
    
    with tab4:
        show_analytics_section(df)

def show_main_dashboard(df):
    """Main analytics dashboard"""
    
    # Filters
    col1, col2 = st.columns(2)
    
    with col1:
        position_filter = st.selectbox(
            "Position:", 
            ["All"] + sorted(df['position'].unique().tolist())
        )
    
    with col2:
        min_price, max_price = st.slider(
            "Price Range:",
            min_value=float(df['price'].min()),
            max_value=float(df['price'].max()),
            value=(4.0, 15.0)
        )
    
    # Apply filters
    filtered_df = df.copy()
    if position_filter != "All":
        filtered_df = filtered_df[filtered_df['position'] == position_filter]
    
    filtered_df = filtered_df[
        (filtered_df['price'] >= min_price) & 
        (filtered_df['price'] <= max_price)
    ]
    
    # Performance vs Price scatter plot
    st.subheader("📊 Player Performance Analysis")
    
    if not filtered_df.empty:
        fig = px.scatter(
            filtered_df,
            x='price',
            y='total_points',
            color='position',
            size='ownership_pct',
            hover_data=['web_name', 'team_name', 'points_per_game'],
            title='Total Points vs Price (bubble size = ownership %)',
            labels={'price': 'Price (£m)', 'total_points': 'Total Points'}
        )
        
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
    
    # Top performers by position
    st.subheader("🏆 Best Players by Position")
    
    for position in ['GK', 'DEF', 'MID', 'FWD']:
        pos_data = df[df['position'] == position].nlargest(3, 'total_points')
        if not pos_data.empty:
            st.write(f"**{position}:**")
            cols = st.columns(3)
            for i, (_, player) in enumerate(pos_data.iterrows()):
                with cols[i]:
                    st.metric(
                        f"{player['web_name']}",
                        f"£{player['price']:.1f}m",
                        f"{int(player['total_points'])} pts"
                    )

def show_my_team_section(df):
    """Personal team management"""
    st.subheader("👤 My FPL Team")
    
    # Load existing team data
    user_team = get_user_team()
    
    # Input FPL manager ID
    default_manager_id = user_team['manager_id'] if user_team and user_team.get('manager_id') else 1
    default_team_name = user_team['team_name'] if user_team and user_team.get('team_name') else ""
    
    manager_id = st.number_input(
        "Enter your FPL Manager ID:", 
        min_value=1, 
        value=default_manager_id,
        help="Find this in your FPL URL: fantasy.premierleague.com/entry/[YOUR_ID]/"
    )
    
    team_name = st.text_input("Team Name (optional):", value=default_team_name)
    
    if st.button("Save My Team Details"):
        if save_user_team(manager_id, team_name):
            st.success("Team details saved!")
        else:
            st.error("Failed to save team details")
    
    # Fetch team data from FPL API
    if manager_id and manager_id > 1:
        try:
            team_url = f"https://fantasy.premierleague.com/api/entry/{manager_id}/"
            response = requests.get(team_url)
            
            if response.status_code == 200:
                team_data = response.json()
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Team Name", team_data.get('name', 'Unknown'))
                
                with col2:
                    st.metric("Total Points", f"{team_data.get('summary_overall_points', 0):,}")
                
                with col3:
                    st.metric("Overall Rank", f"{team_data.get('summary_overall_rank', 0):,}")
                
            else:
                st.warning("Could not fetch team data. Please check your Manager ID.")
        
        except Exception as e:
            st.error(f"Error fetching team: {e}")

def show_transfer_section(df):
    """Transfer planning and suggestions"""
    st.subheader("🔄 Transfer Planning")
    
    # Calculate value scores
    df['value_score'] = df['total_points'] / df['price']
    df['ppg_value'] = df['points_per_game'] / df['price']
    
    # Best value players by position
    st.write("**Best Value Players (Points per £m):**")
    
    for position in ['GK', 'DEF', 'MID', 'FWD']:
        pos_data = df[df['position'] == position].nlargest(5, 'value_score')
        if not pos_data.empty:
            with st.expander(f"{position} - Best Value"):
                st.dataframe(
                    pos_data[['web_name', 'team_name', 'price', 'total_points', 'value_score']],
                    column_config={
                        'web_name': 'Player',
                        'team_name': 'Team',
                        'price': st.column_config.NumberColumn('Price', format="£%.1f"),
                        'total_points': 'Points',
                        'value_score': st.column_config.NumberColumn('Value', format="%.2f")
                    },
                    hide_index=True,
                    use_container_width=True
                )

def show_analytics_section(df):
    """Advanced analytics and insights"""
    st.subheader("📈 Advanced Analytics")
    
    # Current form leaders
    st.write("**Current Form Leaders:**")
    form_leaders = df.nlargest(10, 'form')[
        ['web_name', 'position', 'team_name', 'form', 'total_points']
    ]
    
    if not form_leaders.empty:
        st.dataframe(
            form_leaders,
            column_config={
                'web_name': 'Player',
                'position': 'Pos',
                'team_name': 'Team',
                'form': st.column_config.NumberColumn('Form', format="%.1f"),
                'total_points': 'Total Points'
            },
            hide_index=True,
            use_container_width=True
        )
    
    # Position distribution pie chart
    if not df.empty:
        fig_pos = px.pie(
            df, 
            names='position', 
            title='Player Distribution by Position',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        st.plotly_chart(fig_pos, use_container_width=True)

if __name__ == "__main__":
    main()