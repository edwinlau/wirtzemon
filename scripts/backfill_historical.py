"""
backfill_historical.py

Downloads 2023/24 and 2024/25 season gameweek-by-gameweek data from the
vaastav Fantasy Premier League GitHub archive and upserts it into the
Supabase players_gw_history table.
"""

import os
import sys
import time
import logging
from io import StringIO

import requests
import pandas as pd
from supabase import create_client, Client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY")

SEASONS = {
    "2023-24": 38,
    "2024-25": 38,
}

GW_CSV_URL = (
    "https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League"
    "/master/data/{season}/gws/gw{gw}.csv"
)

TABLE = "players_gw_history"

SOURCE_COLUMNS = {
    "element": "element",
    "name": "name",
    "position": "position",
    "team": "team",
    "total_points": "total_points",
    "minutes": "minutes",
    "goals_scored": "goals_scored",
    "assists": "assists",
    "clean_sheets": "clean_sheets",
    "bonus": "bonus",
    "bps": "bps",
    "influence": "influence",
    "creativity": "creativity",
    "threat": "threat",
    "ict_index": "ict_index",
    "value": "value",
    "selected": "selected",
    "transfers_in": "transfers_in",
    "transfers_out": "transfers_out",
}

INTEGER_COLS = {
    "element", "total_points", "minutes", "goals_scored", "assists",
    "clean_sheets", "bonus", "bps", "value", "selected",
    "transfers_in", "transfers_out",
}

FLOAT_COLS = {"influence", "creativity", "threat", "ict_index"}

BATCH_SIZE = 500


def get_supabase_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        log.error(
            "Missing env vars: SUPABASE_URL and SUPABASE_SERVICE_KEY (or SUPABASE_KEY) required."
        )
        sys.exit(1)
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def fetch_gw_csv(season: str, gw: int):
    url = GW_CSV_URL.format(season=season, gw=gw)
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 404:
            log.warning("GW %d not found for season %s (404) - skipping.", gw, season)
            return None
        resp.raise_for_status()
        return pd.read_csv(StringIO(resp.text))
    except requests.RequestException as exc:
        log.warning("Failed to fetch GW %d for season %s: %s - skipping.", gw, season, exc)
        return None


def normalise_rows(df: pd.DataFrame, season: str, gw: int) -> list:
    rows = []
    for _, row in df.iterrows():
        record = {"season": season, "gameweek": gw}
        for src_col, dst_col in SOURCE_COLUMNS.items():
            if src_col in df.columns:
                val = row[src_col]
                if pd.isna(val):
                    val = None
                elif dst_col in INTEGER_COLS:
                    try:
                        val = int(val)
                    except (ValueError, TypeError):
                        val = None
                elif dst_col in FLOAT_COLS:
                    try:
                        val = float(val)
                    except (ValueError, TypeError):
                        val = None
                record[dst_col] = val
            else:
                record[dst_col] = None
        rows.append(record)
    return rows


def upsert_batch(client: Client, records: list) -> None:
    client.table(TABLE).upsert(records, on_conflict="season,gameweek,element").execute()


def backfill_season(client: Client, season: str, max_gw: int) -> int:
    total = 0
    for gw in range(1, max_gw + 1):
        log.info("Season %s - fetching GW %d ...", season, gw)
        df = fetch_gw_csv(season, gw)
        if df is None or df.empty:
            continue
        records = normalise_rows(df, season, gw)
        if not records:
            continue
        for i in range(0, len(records), BATCH_SIZE):
            chunk = records[i : i + BATCH_SIZE]
            try:
                upsert_batch(client, chunk)
                total += len(chunk)
            except Exception as exc:
                log.error("Upsert failed for season %s GW %d (batch %d): %s", season, gw, i, exc)
        time.sleep(0.3)
    return total


def main() -> None:
    log.info("Starting historical backfill.")
    client = get_supabase_client()
    grand_total = 0
    for season, max_gw in SEASONS.items():
        log.info("=== Backfilling season %s (up to GW %d) ===", season, max_gw)
        n = backfill_season(client, season, max_gw)
        log.info("Season %s complete - %d records upserted.", season, n)
        grand_total += n
    log.info("Backfill complete. Total records upserted: %d", grand_total)


if __name__ == "__main__":
    main()
