# CineTrack

A personal movie recommendation & watch-tracking website, built with Python,
Streamlit, and CSV files (no database required).

## Files
- `app.py` — the entire website (run this).
- `movies.csv` — starter movie catalog.
- `watchlist.csv` / `watched.csv` — created automatically the first time you run the app.
- `.streamlit/config.toml` — dark theme (black background, gold titles, white text).

## How to run
1. Install Python 3.9+ from https://python.org (check "Add Python to PATH" during install on Windows).
2. Open a terminal in this folder.
3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
4. Start the app:
   ```
   streamlit run app.py
   ```
5. Your browser will open automatically to something like `http://localhost:8501`.
   That IS the working website — this is the link/screen to show the professor.

## Resetting your data
Delete `watchlist.csv` and `watched.csv` — the app recreates empty versions
automatically next time it runs.
