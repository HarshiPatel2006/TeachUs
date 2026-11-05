# TeachUs

TeachUs is a Streamlit classroom attendance app. Teachers create subjects, share join codes, enrol students, capture class photos or voice roll calls, review/override attendance, and export history. Students join subjects, save face photos, and see their attendance history.

## Run locally

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Local mode uses SQLite at `data/teachus.db`; passwords are salted PBKDF2-SHA256 hashes. Cloud mode can use Supabase by copying `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`, filling in credentials, and running `supabase/schema.sql` in the SQL editor.

## Deploy on Streamlit Community Cloud

1. Push this repository to GitHub.
2. In Streamlit Community Cloud choose **New app**, select the repository, branch, and `app.py`.
3. Open Advanced settings → Secrets and paste `SUPABASE_URL` and `SUPABASE_KEY`.
4. Deploy, then verify account creation, subject joining, attendance capture, and CSV export.

Never commit real secrets or the local `data/` directory.
