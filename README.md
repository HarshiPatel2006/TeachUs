# TeachUs
Streamlit classroom attendance with teacher/student accounts, subject join codes, salted password hashes, SQLite persistence, and photo/audio capture.

## Local run
`python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt && streamlit run app.py`

Data is stored in `data/teachus.db`. For Cloud, create a Streamlit app using `app.py`, add `SUPABASE_URL` and `SUPABASE_KEY` in Advanced settings → Secrets, then deploy. Never commit real secrets.
