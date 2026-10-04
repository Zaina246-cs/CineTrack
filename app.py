"""
CineTrack - a simple movie recommendation & tracking website.
 
Built with Streamlit (for the website itself) and Pandas (for reading/
writing the CSV files that store all the data). No database is used -
everything lives in plain CSV files so the project stays easy to read.
 
Data files:
- movies.csv     -> the movie catalog (title, genres, year, rating)
- watchlist.csv  -> movies the user wants to watch (created on first run)
- watched.csv    -> movies the user has watched + the user's own rating
"""
 
import random
import pandas as pd
import streamlit as st
from datetime import date
import os
 
# ---------------------------------------------------------------------------
# File paths - keeping these as constants makes them easy to change later
# ---------------------------------------------------------------------------
MOVIES_FILE = "movies.csv"
WATCHLIST_FILE = "watchlist.csv"
WATCHED_FILE = "watched.csv"
 
 
# ---------------------------------------------------------------------------
# Data loading helpers
# ---------------------------------------------------------------------------
 
def load_movies():
    """Load the movie catalog from CSV into a DataFrame."""
    return pd.read_csv(MOVIES_FILE)
 
 
def load_watchlist():
    """Load the user's watchlist. Creates an empty file first if missing."""
    if not os.path.exists(WATCHLIST_FILE):
        pd.DataFrame(columns=["title"]).to_csv(WATCHLIST_FILE, index=False)
    return pd.read_csv(WATCHLIST_FILE)
 
 
def load_watched():
    """Load the user's watched/rated movies. Creates an empty file if missing."""
    if not os.path.exists(WATCHED_FILE):
        pd.DataFrame(columns=["title", "rating", "date_watched"]).to_csv(
            WATCHED_FILE, index=False
        )
    return pd.read_csv(WATCHED_FILE)
 
 
# ---------------------------------------------------------------------------
# Data writing helpers (actions the user can take)
# ---------------------------------------------------------------------------
 
def add_to_watchlist(title):
    """Add a movie title to the watchlist, unless it's already there."""
    watchlist = load_watchlist()
    if title in watchlist["title"].values:
        return  # already on the list, nothing to do
    new_row = pd.DataFrame([{"title": title}])
    watchlist = pd.concat([watchlist, new_row], ignore_index=True)
    watchlist.to_csv(WATCHLIST_FILE, index=False)
 
 
def remove_from_watchlist(title):
    """Remove a movie title from the watchlist."""
    watchlist = load_watchlist()
    watchlist = watchlist[watchlist["title"] != title]
    watchlist.to_csv(WATCHLIST_FILE, index=False)
 
 
def mark_as_watched(title, user_rating):
    """
    Record a movie as watched with the user's rating.
    Also removes it from the watchlist, since it's no longer "to watch".
    """
    watched = load_watched()
    # If it was rated before, update the rating instead of duplicating it
    watched = watched[watched["title"] != title]
    new_row = pd.DataFrame([{
        "title": title,
        "rating": user_rating,
        "date_watched": date.today().isoformat(),
    }])
    watched = pd.concat([watched, new_row], ignore_index=True)
    watched.to_csv(WATCHED_FILE, index=False)
    remove_from_watchlist(title)
 
 
# ---------------------------------------------------------------------------
# Recommendation logic
# ---------------------------------------------------------------------------
 
def get_all_genres(movies):
    """Return a sorted list of every unique genre in the catalog."""
    genre_set = set()
    for genre_string in movies["genres"]:
        for genre in genre_string.split(","):
            genre_set.add(genre.strip())
    return sorted(genre_set)
 
 
def recommend_by_genre(movies, genre, limit=10):
    """Return top-rated movies that include the given genre."""
    matches = movies[movies["genres"].str.contains(genre, case=False)]
    return matches.sort_values("rating", ascending=False).head(limit)
 
 
def random_recommendation(movies):
    """Pick one random movie from the whole catalog."""
    return movies.sample(1).iloc[0]
 
 
def recommend_based_on_watched(movies, watched, limit=10):
    """
    Simple content-based recommendation:
    1. Look at the genres of movies the user rated highly (4+ out of 5... or
       adjust the threshold below if you use a different rating scale).
    2. Suggest unwatched movies that share those genres, best-rated first.
    """
    if watched.empty:
        return pd.DataFrame()  # nothing to base a recommendation on yet
 
    liked = watched[watched["rating"] >= 4]
    if liked.empty:
        return pd.DataFrame()
 
    liked_titles = liked["title"].tolist()
    liked_movies = movies[movies["title"].isin(liked_titles)]
 
    favorite_genres = set()
    for genre_string in liked_movies["genres"]:
        for genre in genre_string.split(","):
            favorite_genres.add(genre.strip())
 
    watched_titles = watched["title"].tolist()
    unwatched = movies[~movies["title"].isin(watched_titles)]
 
    def shares_a_favorite_genre(genre_string):
        movie_genres = [g.strip() for g in genre_string.split(",")]
        return any(g in favorite_genres for g in movie_genres)
 
    matches = unwatched[unwatched["genres"].apply(shares_a_favorite_genre)]
    return matches.sort_values("rating", ascending=False).head(limit)
 
 
# ---------------------------------------------------------------------------
# Small reusable UI piece: a movie "card"
# ---------------------------------------------------------------------------
 
def show_movie_card(movie, key_prefix):
    """
    Display one movie with an 'Add to Watchlist' button.
    key_prefix keeps Streamlit button keys unique across the app.
    """
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f"**{movie['title']}** ({movie['year']})")
        st.caption(f"Genres: {movie['genres']} | Rating: {movie['rating']}/10")
    with col2:
        if st.button("+ Watchlist", key=f"{key_prefix}_{movie['title']}"):
            add_to_watchlist(movie["title"])
            st.success("Added!")
 
 
# ---------------------------------------------------------------------------
# Page setup + custom styling (black background, gold titles, white text)
# ---------------------------------------------------------------------------
 
st.set_page_config(page_title="CineTrack", page_icon="🎬", layout="centered")
 
st.markdown(
    """
    <style>
    h1, h2, h3 { color: #FFD700 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)
 
movies = load_movies()
 
st.title("🎬 CineTrack")
st.caption("Your personal movie recommendation and watch tracker")
 
page = st.sidebar.radio(
    "Navigate",
    ["Home", "Discover", "Genre Search", "Random Pick", "My Watchlist", "Watched & Ratings"],
)
 
# ---------------------------------------------------------------------------
# HOME
# ---------------------------------------------------------------------------
if page == "Home":
    st.header("Welcome to CineTrack")
    st.write(
        "Use the sidebar to discover movies, search by genre, get a random "
        "pick, manage your watchlist, or rate movies you've already seen."
    )
    watchlist = load_watchlist()
    watched = load_watched()
    col1, col2 = st.columns(2)
    col1.metric("Movies in your watchlist", len(watchlist))
    col2.metric("Movies you've rated", len(watched))
 
# ---------------------------------------------------------------------------
# DISCOVER (personalized, based on watched/rated movies)
# ---------------------------------------------------------------------------
elif page == "Discover":
    st.header("Discover")
    st.write("Recommendations based on movies you've rated highly (4-5 stars).")
    watched = load_watched()
    suggestions = recommend_based_on_watched(movies, watched)
 
    if suggestions.empty:
        st.info(
            "Rate a few movies in 'Watched & Ratings' first, and CineTrack "
            "will start recommending movies like the ones you loved."
        )
    else:
        for _, movie in suggestions.iterrows():
            show_movie_card(movie, "discover")
 
# ---------------------------------------------------------------------------
# GENRE SEARCH
# ---------------------------------------------------------------------------
elif page == "Genre Search":
    st.header("Search by Genre")
    genres = get_all_genres(movies)
    chosen_genre = st.selectbox("Pick a genre", genres)
 
    if chosen_genre:
        results = recommend_by_genre(movies, chosen_genre)
        st.write(f"Top {chosen_genre} movies:")
        for _, movie in results.iterrows():
            show_movie_card(movie, "genre")
 
# ---------------------------------------------------------------------------
# RANDOM PICK
# ---------------------------------------------------------------------------
elif page == "Random Pick":
    st.header("Feeling Lucky?")
    if st.button("🎲 Surprise Me"):
        pick = random_recommendation(movies)
        st.subheader(pick["title"])
        st.write(f"**Year:** {pick['year']}")
        st.write(f"**Genres:** {pick['genres']}")
        st.write(f"**Rating:** {pick['rating']}/10")
        if st.button("+ Add to Watchlist", key="random_add"):
            add_to_watchlist(pick["title"])
            st.success("Added to your watchlist!")
 
# ---------------------------------------------------------------------------
# MY WATCHLIST
# ---------------------------------------------------------------------------
elif page == "My Watchlist":
    st.header("My Watchlist")
    watchlist = load_watchlist()
 
    if watchlist.empty:
        st.info("Your watchlist is empty. Add movies from Discover, Genre Search, or Random Pick.")
    else:
        for title in watchlist["title"]:
            movie_row = movies[movies["title"] == title]
            if movie_row.empty:
                continue
            movie = movie_row.iloc[0]
 
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"**{movie['title']}** ({movie['year']})")
                st.caption(f"Genres: {movie['genres']}")
            with col2:
                rating_choice = st.selectbox(
                    "Rate", [1, 2, 3, 4, 5], key=f"rate_{title}", label_visibility="collapsed"
                )
            with col3:
                if st.button("Mark Watched", key=f"watched_{title}"):
                    mark_as_watched(title, rating_choice)
                    st.success(f"Marked '{title}' as watched!")
                    st.rerun()
 
            if st.button("Remove", key=f"remove_{title}"):
                remove_from_watchlist(title)
                st.rerun()
 
# ---------------------------------------------------------------------------
# WATCHED & RATINGS
# ---------------------------------------------------------------------------
elif page == "Watched & Ratings":
    st.header("Watched & Ratings")
 
    st.subheader("Rate a movie you've watched")
    all_titles = movies["title"].tolist()
    selected_title = st.selectbox("Movie", all_titles)
    rating = st.slider("Your rating", 1, 5, 3)
    if st.button("Save Rating"):
        mark_as_watched(selected_title, rating)
        st.success(f"Saved your rating for '{selected_title}'!")
        st.rerun()
 
    st.subheader("Your rated movies")
    watched = load_watched()
    if watched.empty:
        st.info("You haven't rated any movies yet.")
    else:
        sort_choice = st.radio("Sort by", ["Rating", "Date watched"], horizontal=True)
        if sort_choice == "Rating":
            watched = watched.sort_values("rating", ascending=False)
        else:
            watched = watched.sort_values("date_watched", ascending=False)
 
        for _, row in watched.iterrows():
            st.write(f"**{row['title']}** — {row['rating']}/5 stars (watched {row['date_watched']})")
 