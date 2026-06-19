
import pickle

import requests
import streamlit as st

# TMDB API KEY
TMDB_API_KEY = "223e903d4afa44f2fadf7fa113190728"

st.set_page_config(
    page_title="Movie Recommender",
    page_icon="🎬",
    layout="wide",
)

PLACEHOLDER_POSTER = (
    "https://via.placeholder.com/300x450.png?text=No+Poster"
)

def fetch_poster(movie_title: str) -> str:
    """
    Search TMDB for the movie title and return the poster URL.
    Falls back to a placeholder if anything goes wrong.
    """
    if TMDB_API_KEY == "YOUR_TMDB_API_KEY_HERE":
        return PLACEHOLDER_POSTER

    try:
        # Step 1 — search for the movie
        search_url = "https://api.themoviedb.org/3/search/movie"
        params = {
            "api_key": TMDB_API_KEY,
            "query": movie_title,
            "language": "en-US",
            "page": 1,
        }
        response = requests.get(search_url, params=params, timeout=5)
        response.raise_for_status()
        results = response.json().get("results", [])

        if not results:
            return PLACEHOLDER_POSTER

        # Step 2 — grab the poster path of the top result
        poster_path = results[0].get("poster_path")
        if poster_path:
            return f"https://image.tmdb.org/t/p/w500{poster_path}"

        return PLACEHOLDER_POSTER

    except requests.exceptions.RequestException:
        return PLACEHOLDER_POSTER



@st.cache_resource
def load_data():
    """Load the pre-built movie list and similarity matrix from disk."""
    try:
        with open("movies_list.pkl", "rb") as f:
            movies = pickle.load(f)
        with open("similarity.pkl", "rb") as f:
            similarity = pickle.load(f)
        return movies, similarity
    except FileNotFoundError as e:
        st.error(
            f"⚠️  Required file not found: {e}\n\n"
            "Please run **Movies_Recommended.py** first to generate the pickle files."
        )
        st.stop()


movies, similarity = load_data()


def recommend(selected_title: str, top_n: int = 5):
    """
    Return the top-N most similar movie titles and their poster URLs.

    Parameters
    ----------
    selected_title : str
        The movie title chosen by the user.
    top_n : int
        Number of recommendations to return.
    """
    # Find the row index that matches the selected title
    matches = movies[movies["title"] == selected_title]
    if matches.empty:
        st.warning("Movie not found in dataset.")
        return [], []

    index = matches.index[0]

    # Sort all movies by similarity score (descending), skip the movie itself
    distances = sorted(
        enumerate(similarity[index]),
        key=lambda x: x[1],
        reverse=True,
    )

    rec_titles  = []
    rec_posters = []

    for movie_index, _score in distances[1 : top_n + 1]:
        title = movies.iloc[movie_index]["title_clean"]
        rec_titles.append(title)
        rec_posters.append(fetch_poster(title))

    return rec_titles, rec_posters




st.markdown(
    """
    <style>
    [data-testid="stImage"] img {
        width: 150px !important;
        height: 220px !important;
        object-fit: cover;
        border-radius: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🎬 Movie Recommender System")
st.markdown(
    "Select a movie below and click **Show Recommendations** "
    "to get 5 similar films."
)

movie_titles = movies["title"].values
selected_movie = st.selectbox("Choose a movie:", movie_titles)

if st.button("Show Recommendations", type="primary"):
    with st.spinner("Finding similar movies …"):
        names, posters = recommend(selected_movie)

    if names:
        st.subheader("You might also like:")
        cols = st.columns(5)
        for col, name, poster in zip(cols, names, posters):
            with col:
                st.image(poster, width=150)
                st.caption(name)

