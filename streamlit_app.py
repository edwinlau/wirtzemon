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