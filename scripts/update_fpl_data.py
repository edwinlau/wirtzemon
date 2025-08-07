# scripts/update_fpl_data.py
# Automated FPL Data Pipeline with Change Data Capture

import os
import requests
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import logging
import json

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FPLDataUpdater:
    def __init__(self):
        # Initialize Supabase client with service key for full access
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Missing Supabase credentials")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        self.update_id = None
        
    def log_update_start(self, update_type='scheduled'):
        """Log the start of an update process"""
        try:
            result = self.supabase.table('data_updates').insert({
                'update_type': update_type,
                'status': 'running',
                'triggered_by': 'github_action',
                'started_at': datetime.now().isoformat()
            }).execute()
            
            self.update_id = result.data[0]['id'] if result.data else None
            logger.info(f"Started update process with ID: {self.update_id}")
            
        except Exception as e:
            logger.error(f"Failed to log update start: {e}")
    
    def log_update_complete(self, status, players_updated=0, changes_detected=0, error_message=None):
        """Log the completion of an update process"""
        if not self.update_id:
            return
            
        try:
            self.supabase.table('data_updates').update({
                'status': status,
                'players_updated': players_updated,
                'changes_detected': changes_detected,
                'error_message': error_message,
                'completed_at': datetime.now().isoformat()
            }).eq('id', self.update_id).execute()
            
            logger.info(f"Update {self.update_id} completed with status: {status}")
            
        except Exception as e:
            logger.error(f"Failed to log update completion: {e}")
    
    def fetch_fpl_data(self):
        """Fetch latest FPL data from official API"""
        try:
            logger.info("Fetching latest FPL data...")
            
            # Main bootstrap data
            bootstrap_url = "https://fantasy.premierleague.com/api/bootstrap-static/"
            response = requests.get(bootstrap_url)
            response.raise_for_status()
            data = response.json()
            
            # Extract current gameweek info
            events = data['events']
            current_gw = next((event['id'] for event in events if event['is_current']), None)
            
            # Process player data
            players = data['elements']
            teams = data['teams']
            positions = data['element_types']
            
            # Create lookups
            team_lookup = {team['id']: team['name'] for team in teams}
            position_lookup = {pos['id']: pos['singular_name_short'] for pos in positions}
            
            # Convert to DataFrame with all available fields
            df = pd.DataFrame(players)
            df['team_name'] = df['team'].map(team_lookup)
            df['position'] = df['element_type'].map(position_lookup)
            df['current_gameweek'] = current_gw
            
            logger.info(f"Successfully fetched data for {len(df)} players (GW {current_gw})")
            return df, current_gw
            
        except Exception as e:
            logger.error(f"Failed to fetch FPL data: {e}")
            raise
    
    def get_current_database_data(self):
        """Get current player data from database"""
        try:
            logger.info("Fetching current database data...")
            result = self.supabase.table('players_current').select('*').execute()
            
            if result.data:
                df = pd.DataFrame(result.data)
                logger.info(f"Found {len(df)} players in database")
                return df
            else:
                logger.info("No existing data in database")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Failed to fetch database data: {e}")
            return pd.DataFrame()
    
    def detect_changes(self, new_data, current_data, gameweek):
        """Detect changes between new and current data"""
        changes = []
        price_changes = []
        
        if current_data.empty:
            logger.info("No existing data - treating all as new")
            return [], []
        
        logger.info("Detecting changes...")
        
        for _, new_player in new_data.iterrows():
            player_id = int(new_player['id'])
            
            # Find current player data
            current_player = current_data[current_data['id'] == player_id]
            
            if current_player.empty:
                # New player
                changes.append({
                    'player_id': player_id,
                    'gameweek': gameweek,
                    'change_type': 'new_player',
                    'web_name': new_player['web_name'],
                    'position': new_player['position'],
                    'team_name': new_player['team_name'],
                    'now_cost': int(new_player['now_cost']),
                    'total_points': int(new_player['total_points']),
                    'points_per_game': float(new_player['points_per_game']) if pd.notna(new_player['points_per_game']) else 0.0,
                    'selected_by_percent': float(new_player['selected_by_percent']),
                    'form': float(new_player['form']) if pd.notna(new_player['form']) else 0.0,
                    'recorded_at': datetime.now().isoformat()
                })
                continue
            
            current = current_player.iloc[0]
            
            # Check for price changes
            old_price = current['now_cost']
            new_price = int(new_player['now_cost'])
            
            if old_price != new_price:
                price_change = (new_price - old_price) / 10  # Convert to £m
                price_changes.append({
                    'player_id': player_id,
                    'old_price': old_price / 10,
                    'new_price': new_price / 10,
                    'price_change': price_change,
                    'ownership_percent': float(new_player['selected_by_percent']),
                    'gameweek': gameweek,
                    'change_date': datetime.now().isoformat()
                })
                
                changes.append({
                    'player_id': player_id,
                    'gameweek': gameweek,
                    'change_type': 'price_change',
                    'web_name': new_player['web_name'],
                    'now_cost': new_price,
                    'recorded_at': datetime.now().isoformat()
                })
            
            # Check for points changes
            if current['total_points'] != int(new_player['total_points']):
                changes.append({
                    'player_id': player_id,
                    'gameweek': gameweek,
                    'change_type': 'points_update',
                    'web_name': new_player['web_name'],
                    'total_points': int(new_player['total_points']),
                    'recorded_at': datetime.now().isoformat()
                })
            
            # Check for form changes (if significant)
            old_form = float(current['form']) if pd.notna(current['form']) else 0.0
            new_form = float(new_player['form']) if pd.notna(new_player['form']) else 0.0
            
            if abs(old_form - new_form) > 0.1:  # Only log significant form changes
                changes.append({
                    'player_id': player_id,
                    'gameweek': gameweek,
                    'change_type': 'form_change',
                    'web_name': new_player['web_name'],
                    'form': new_form,
                    'recorded_at': datetime.now().isoformat()
                })
        
        logger.info(f"Detected {len(changes)} changes and {len(price_changes)} price changes")
        return changes, price_changes
    
    def store_changes(self, changes, price_changes):
        """Store detected changes in database"""
        stored_changes = 0
        stored_price_changes = 0
        
        try:
            # Store general changes
            if changes:
                result = self.supabase.table('player_history').insert(changes).execute()
                stored_changes = len(result.data) if result.data else 0
                logger.info(f"Stored {stored_changes} player changes")
            
            # Store price changes
            if price_changes:
                result = self.supabase.table('price_changes').insert(price_changes).execute()
                stored_price_changes = len(result.data) if result.data else 0
                logger.info(f"Stored {stored_price_changes} price changes")
                
        except Exception as e:
            logger.error(f"Failed to store changes: {e}")
            raise
        
        return stored_changes + stored_price_changes
    
    def update_current_data(self, new_data):
        """Update the current players table with latest data"""
        try:
            logger.info("Updating current player data...")
            
            # Prepare data for upsert
            players_data = []
            for _, row in new_data.iterrows():
                players_data.append({
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
                    'goals_conceded': int(row['goals_conceded']),
                    'own_goals': int(row['own_goals']),
                    'penalties_saved': int(row['penalties_saved']),
                    'penalties_missed': int(row['penalties_missed']),
                    'yellow_cards': int(row['yellow_cards']),
                    'red_cards': int(row['red_cards']),
                    'saves': int(row['saves']),
                    'bonus': int(row['bonus']),
                    'bps': int(row['bps']),
                    'influence': float(row['influence']) if pd.notna(row['influence']) else 0.0,
                    'creativity': float(row['creativity']) if pd.notna(row['creativity']) else 0.0,
                    'threat': float(row['threat']) if pd.notna(row['threat']) else 0.0,
                    'ict_index': float(row['ict_index']) if pd.notna(row['ict_index']) else 0.0,
                    'dreamteam_count': int(row['dreamteam_count']),
                    'in_dreamteam': bool(row['in_dreamteam']),
                    'updated_at': datetime.now().isoformat()
                })
            
            # Batch upsert
            result = self.supabase.table('players_current').upsert(players_data).execute()
            players_updated = len(result.data) if result.data else 0
            
            logger.info(f"Updated {players_updated} players in current data table")
            return players_updated
            
        except Exception as e:
            logger.error(f"Failed to update current data: {e}")
            raise
    
    def run_update(self):
        """Main update process"""
        try:
            # Start logging
            self.log_update_start()
            
            # Fetch latest FPL data
            new_data, gameweek = self.fetch_fpl_data()
            
            # Get current database data
            current_data = self.get_current_database_data()
            
            # Detect changes
            changes, price_changes = self.detect_changes(new_data, current_data, gameweek)
            
            # Store changes
            changes_stored = self.store_changes(changes, price_changes)
            
            # Update current data
            players_updated = self.update_current_data(new_data)
            
            # Log success
            self.log_update_complete('success', players_updated, changes_stored)
            
            logger.info(f"Update completed successfully!")
            logger.info(f"Players updated: {players_updated}")
            logger.info(f"Changes detected and stored: {changes_stored}")
            
            # Print summary for GitHub Actions logs
            print(f"✅ FPL Data Update Successful")
            print(f"📊 Players updated: {players_updated}")
            print(f"🔄 Changes detected: {changes_stored}")
            print(f"⚽ Current gameweek: {gameweek}")
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Update failed: {error_msg}")
            self.log_update_complete('failed', error_message=error_msg)
            
            print(f"❌ FPL Data Update Failed: {error_msg}")
            raise

if __name__ == "__main__":
    updater = FPLDataUpdater()
    updater.run_update()
