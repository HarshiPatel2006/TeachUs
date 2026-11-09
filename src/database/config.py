"""Backend configuration. Secrets stay on the Streamlit server."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.environ.get('TEACHUS_DATA_DIR', ROOT / 'data'))
DB_PATH = DATA_DIR / 'teachus.db'
BUCKET = 'face-photos'


def credentials():
    import streamlit as st
    try:
        return st.secrets.get('SUPABASE_URL', ''), st.secrets.get('SUPABASE_KEY', '')
    except (FileNotFoundError, KeyError):
        return '', ''


def use_supabase():
    url, key = credentials()
    if bool(url) != bool(key):
        raise ValueError('Set both SUPABASE_URL and SUPABASE_KEY, or remove both.')
    return bool(url and key)
