import pandas as pd
import streamlit as st

# Try importing plotly safely
try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="Top 50 Playlist Dashboard", layout="wide")
st.title("🎵 Top 50 Playlist Analytics")

if not PLOTLY_AVAILABLE:
    st.error("Plotly is not installed. Add 'plotly' to requirements.txt or run: pip install plotly")
    st.stop()

# =========================
# LOAD DATA
# =========================
@st.cache_data
def load_data(file):
    df = pd.read_csv(file)

    required = [
        'date','position','song','artist','popularity',
        'duration_ms','album_type','total_tracks',
        'is_explicit','album_cover_url'
    ]

    missing = [c for c in required if c not in df.columns]
    if missing:
        st.error(f"Missing columns: {missing}")
        return None

    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date'])

    df['song'] = df['song'].astype(str).str.strip()
    df['artist'] = df['artist'].astype(str).str.strip()

    df['song_id'] = df['song'] + " - " + df['artist']

    return df


# =========================
# UPLOAD
# =========================
file = st.file_uploader("Upload your CSV file", type=["csv"])

if file:
    df = load_data(file)
    if df is None:
        st.stop()

    # =========================
    # FILTERS
    # =========================
    st.sidebar.header("Filters")

    min_date, max_date = df['date'].min(), df['date'].max()
    date_range = st.sidebar.date_input("Date Range", [min_date, max_date])

    df = df[
        (df['date'] >= pd.to_datetime(date_range[0])) &
        (df['date'] <= pd.to_datetime(date_range[1]))
    ]

    artists = st.sidebar.multiselect("Select Artist", df['artist'].unique())
    if artists:
        df = df[df['artist'].isin(artists)]

    selected_song = st.sidebar.selectbox("Select Song", df['song_id'].unique())

    # =========================
    # KPIs
    # =========================
    st.subheader("Overview")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Songs", df['song_id'].nunique())
    col2.metric("Records", len(df))
    col3.metric("Avg Popularity", round(df['popularity'].mean(), 2))
    col4.metric("Avg Duration (min)", round(df['duration_ms'].mean()/60000, 2))

    st.divider()

    # =========================
    # TOP SONGS
    # =========================
    st.subheader("Top Songs (Balanced Score)")

    summary = df.groupby('song_id').agg(
        avg_pop=('popularity','mean'),
        best_pos=('position','min'),
        days=('date','nunique')
    ).reset_index()

    summary['score'] = (
        summary['avg_pop'] * 0.4 +
        (50 - summary['best_pos']) * 0.4 +
        summary['days'] * 0.2
    )

    top_n = st.slider("Top N Songs", 5, 50, 10)
    st.dataframe(summary.sort_values('score', ascending=False).head(top_n))

    st.divider()

    # =========================
    # SONG ANALYSIS
    # =========================
    st.subheader("Song Analysis")

    song_df = df[df['song_id'] == selected_song].sort_values('date')

    if not song_df.empty:

        col1, col2 = st.columns([1,2])

        with col1:
            st.image(song_df['album_cover_url'].iloc[0], caption=selected_song)

        with col2:
            fig1 = px.line(song_df, x='date', y='position', title="Chart Position")
            fig1.update_yaxes(autorange="reversed")
            st.plotly_chart(fig1, use_container_width=True)

        fig2 = px.line(song_df, x='date', y='popularity', title="Popularity Trend")
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    # =========================
    # CONTENT INSIGHTS
    # =========================
    st.subheader("Content Insights")

    col1, col2 = st.columns(2)

    with col1:
        fig3 = px.histogram(df, x='popularity', nbins=20, title="Popularity Distribution")
        st.plotly_chart(fig3, use_container_width=True)

    with col2:
        explicit_df = df.groupby('is_explicit')['song_id'].nunique().reset_index()
        fig4 = px.bar(explicit_df, x='is_explicit', y='song_id', title="Explicit vs Clean Songs")
        st.plotly_chart(fig4, use_container_width=True)

    st.divider()

    # =========================
    # TREND VIEW
    # =========================
    st.subheader("Chart Trends")

    fig5 = px.line(df, x='date', y='position', color='song_id',
                   title="Song Ranking Over Time")
    fig5.update_yaxes(autorange="reversed")
    st.plotly_chart(fig5, use_container_width=True)

else:
    st.info("Upload your CSV file to begin")
