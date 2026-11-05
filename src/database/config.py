import os
from pathlib import Path

DATA_DIR = Path(os.getenv("TEACHUS_DATA_DIR", "data"))
DB_PATH = DATA_DIR / "teachus.db"

def use_supabase():
    try:
        import streamlit as st
        return bool(st.secrets.get("SUPABASE_URL") and st.secrets.get("SUPABASE_KEY"))
    except Exception:
        return bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_KEY"))
