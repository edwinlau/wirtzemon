# scripts/update_defcon_data.py
# Automated DefCon data pipeline for GitHub Actions

import os
import requests
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import logging
from bs4 import BeautifulSoup
import time
import numpy as np

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DefConDataUpdater:
    def __init__(self):
        # Initialize Supabase client
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Missing Supabase credentials")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        
        # FBref scraping setup
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        self.base_url = "https://fbref.com"
        self.season = "2024-25"
        
    def fetch_fbref_defensive_stats(self):
        """Fetch defensive statistics from FBref"""
        
        try:
            logger.info("Fetching defensive stats from FBref...")
            
            # Defensive stats URL
            url = f"{self.base_url}/en/comps/9/{self.season}/defense/Premier-League-Stats"
            
            response = self.session.get(url)
            response.raise_for_status()
            
            # Parse HTML and extract defensive stats table
            soup = BeautifulSoup(response.content, 'html.parser')
            table = soup.find('table', {'id': 'stats_defense'})
            
            if not table:
                logger.error("Could not find defensive stats table")
                return None
            
            # Convert to DataFrame
            df = pd.read_html(str(table))[0]
            
            # Clean multi-level columns
            df.columns = [col[1] if col[1] != '' else col[0] for col in df.columns]
            
            # Remove header rows and clean data
            df = df[df['Player'] != 'Player'].reset_index(drop=True)
            
            # Convert numeric columns
            numeric_cols = ['MP', '90s', 'Tkl', 'TklW', 'Int', 'Blocks', 'Clr']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            logger.info(f"Successfully fetched defensive stats for {len(df)} players")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching FBref defensive stats: {e}")
            return None
    
    def fetch_fbref_possession_stats(self):
        """Fetch possession stats (for ball recoveries) from FBref"""
        
        try:
            logger.info("Fetching possession stats from FBref...")
            
            # Add delay to be respectful to FBref servers
            time.sleep(2)
            
            url = f"{self.base_url}/en/comps/9/{self.season}/possession/Premier-League-Stats"
            
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            table = soup.find('table', {'id': 'stats_possession'})
            
            if not table:
                logger.warning("Could not find possession stats table")
                return None
            
            df = pd.read_html(str(table))[0]
            df.columns = [col[1] if col[1] != '' else col[0] for col in df.columns]
            
            # Clean and extract ball recoveries
            df = df[df['Player'] != 'Player'].reset_index(drop=True)
            
            if 'Recov' in df.columns:
                df['Recov'] = pd.to_numeric(df['Recov'], errors='coerce')
                
            logger.info(f"Successfully fetched possession stats for {len(df)} players")
            return df
            
        except Exception as e:
            logger.warning(f"Could not fetch possession stats: {e}")
            return None
    
    def process_defensive_data(self, defensive_df, possession_df=None):
        """Process and combine defensive and possession data"""
        
        try:
            logger.info("Processing defensive data...")
            
            # Create processed dataframe
            processed_players = []
            
            for _, row in defensive_df.iterrows():
                player_name = str(row.get('Player', '')).strip()
                team_name = str(row.get('Squad', '')).strip()
                
                if not player_name or player_name == 'nan':
                    continue
                
                # Extract position and standardize
                position_raw = str(row.get('Pos', 'MID')).strip()
                position = self.standardize_position(position_raw)
                
                # Get ball recoveries if available
                ball_recoveries = 0
                if possession_df is not None:
                    recovery_match = possession_df[
                        (possession_df['Player'].str.strip() == player_name) & 
                        (possession_df['Squad'].str.strip() == team_name)
                    ]
                    if not recovery_match.empty:
                        ball_recoveries = recovery_match.iloc[0].get('Recov', 0)
                        ball_recoveries = ball_recoveries if pd.notna(ball_recoveries) else 0
                
                # Create player record
                player_data = {
                    'player_name': player_name,
                    'team_name': team_name,
                    'position': position,
                    'season': '2024/25',
                    'matches_played': int(row.get('MP', 0)) if pd.notna(row.get('MP', 0)) else 0,
                    'minutes_90s': float(row.get('90s', 0)) if pd.notna(row.get('90s', 0)) else 0,
                    'clearances': int(row.get('Clr', 0)) if pd.notna(row.get('Clr', 0)) else 0,
                    'blocks': int(row.get('Blocks', 0)) if pd.notna(row.get('Blocks', 0)) else 0,
                    'interceptions': int(row.get('Int', 0)) if pd.notna(row.get('Int', 0)) else 0,
                    'tackles_won': int(row.get('Tkl', 0)) if pd.notna(row.get('Tkl', 0)) else 0,
                    'tackles_attempted': int(row.get('TklW', 0)) if pd.notna(row.get('TklW', 0)) else 0,
                    'ball_recoveries': int(ball_recoveries),
                    'minutes_played': int(float(row.get('90s', 0)) * 90) if pd.notna(row.get('90s', 0)) else 0,
                    'data_source': 'fbref',
                    'last_updated': datetime.now().isoformat()
                }
                
                processed_players.append(player_data)
            
            logger.info(f"Processed {len(processed_players)} player records")
            return processed_players
            
        except Exception as e:
            logger.error(f"Error processing defensive data: {e}")
            return []
    
    def standardize_position(self, position_raw):
        """Standardize position names for DefCon calculations"""
        
        pos_upper = position_raw.upper()
        
        if any(p in pos_upper for p in ['GK']):
            return 'GK'
        elif any(p in pos_upper for p in ['DF', 'CB', 'LB', 'RB', 'WB']):
            return 'DEF'
        elif any(p in pos_upper for p in ['FW', 'CF', 'ST']):
            return 'FWD'
        else:
            return 'MID'
    
    def store_defensive_stats(self, player_data):
        """Store processed defensive stats in Supabase"""
        
        try:
            logger.info(f"Storing {len(player_data)} defensive stat records...")
            
            # Batch upsert to Supabase
            result = self.supabase.table('player_defensive_stats').upsert(player_data).execute()
            
            stored_count = len(result.data) if result.data else 0
            logger.info(f"Successfully stored {stored_count} defensive stat records")
            
            return stored_count
            
        except Exception as e:
            logger.error(f"Error storing defensive stats: {e}")
            return 0
    
    def update_team_defcon_stats(self):
        """Calculate and update team-level DefCon statistics"""
        
        try:
            logger.info("Updating team DefCon statistics...")
            
            # Query individual player stats
            players = self.supabase.table('player_defensive_stats').select('*').execute()
            
            if not players.data:
                logger.warning("No player defensive stats found")
                return
            
            # Group by team and calculate totals
            team_stats = {}
            
            for player in players.data:
                team = player['team_name']
                
                if team not in team_stats:
                    team_stats[team] = {
                        'team_name': team,
                        'season': '2024/25',
                        'total_cbit_actions': 0,
                        'total_cbitr_actions': 0,
                        'total_defcon_points': 0,
                        'matches_played': 0,
                        'gk_defcon_points': 0,
                        'def_defcon_points': 0,
                        'mid_defcon_points': 0,
                        'fwd_defcon_points': 0
                    }
                
                # Add player contributions
                cbit = (player.get('clearances', 0) + player.get('blocks', 0) + 
                       player.get('interceptions', 0) + player.get('tackles_won', 0))
                cbitr = cbit + player.get('ball_recoveries', 0)
                
                team_stats[team]['total_cbit_actions'] += cbit
                team_stats[team]['total_cbitr_actions'] += cbitr
                team_stats[team]['matches_played'] = max(team_stats[team]['matches_played'], 
                                                       player.get('matches_played', 0))
                
                # Add position-specific DefCon points
                defcon_points = player.get('defcon_points_per_game', 0) * player.get('matches_played', 0)
                position = player.get('position', 'MID')
                
                if position == 'GK':
                    team_stats[team]['gk_defcon_points'] += defcon_points
                elif position == 'DEF':
                    team_stats[team]['def_defcon_points'] += defcon_points
                elif position == 'MID':
                    team_stats[team]['mid_defcon_points'] += defcon_points
                elif position == 'FWD':
                    team_stats[team]['fwd_defcon_points'] += defcon_points
                
                team_stats[team]['total_defcon_points'] += defcon_points
            
            # Calculate averages
            team_records = []
            for team_data in team_stats.values():
                matches = max(team_data['matches_played'], 1)
                team_data['avg_cbit_per_game'] = team_data['total_cbit_actions'] / matches
                team_data['avg_cbitr_per_game'] = team_data['total_cbitr_actions'] / matches
                team_data['avg_defcon_points_per_game'] = team_data['total_defcon_points'] / matches
                team_data['last_updated'] = datetime.now().isoformat()
                
                team_records.append(team_data)
            
            # Store team stats
            result = self.supabase.table('team_defcon_stats').upsert(team_records).execute()
            
            logger.info(f"Updated DefCon stats for {len(team_records)} teams")
            
        except Exception as e:
            logger.error(f"Error updating team DefCon stats: {e}")
    
    def run_defcon_update(self):
        """Main DefCon update process"""
        
        try:
            logger.info("Starting DefCon data update...")
            
            # Fetch defensive stats from FBref
            defensive_df = self.fetch_fbref_defensive_stats()
            if defensive_df is None:
                raise Exception("Could not fetch defensive statistics")
            
            # Fetch possession stats (ball recoveries)
            possession_df = self.fetch_fbref_possession_stats()
            
            # Process the data
            processed_data = self.process_defensive_data(defensive_df, possession_df)
            if not processed_data:
                raise Exception("No data was processed")
            
            # Store in database
            stored_count = self.store_defensive_stats(processed_data)
            
            # Update team statistics
            self.update_team_defcon_stats()
            
            logger.info(f"DefCon update completed successfully!")
            logger.info(f"Players updated: {stored_count}")
            
            # Print summary for GitHub Actions
            print(f"✅ DefCon Data Update Successful")
            print(f"📊 Players updated: {stored_count}")
            print(f"🛡️ DefCon stats now available")
            
            return True
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"DefCon update failed: {error_msg}")
            print(f"❌ DefCon Data Update Failed: {error_msg}")
            return False

if __name__ == "__main__":
    updater = DefConDataUpdater()
    success = updater.run_defcon_update()
    
    if not success:
        exit(1)  # Exit with error code for GitHub Actions
