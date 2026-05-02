import pandas as pd
import streamlit as st

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="Top 50 Playlist Dashboard", layout="wide")
st.title("🎵 Top 50 Playlist Analytics (No Plotly Version)")

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
# UPLOAD FILE
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
    # KPI
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
    # SONG ANALYSIS (TABLE + SIMPLE CHARTS)
    # =========================
    st.subheader("Song Analysis")

    song_df = df[df['song_id'] == selected_song].sort_values('date')

    if not song_df.empty:

        col1, col2 = st.columns([1,2])

        with col1:
            st.image(song_df['album_cover_url'].iloc[0], caption=selected_song)

            st.write("### Data Table")
            st.dataframe(song_df[['date','position','popularity']])

        with col2:
            st.write("### Position Trend (Line)")
            st.line_chart(song_df.set_index('date')['position'])

            st.write("### Popularity Trend (Line)")
            st.line_chart(song_df.set_index('date')['popularity'])

        st.write("**Best Rank:**", song_df['position'].min())
        st.write("**Days on Chart:**", song_df['date'].nunique())
        st.write("**Avg Popularity:**", round(song_df['popularity'].mean(), 2))

    st.divider()

    # =========================
    # CONTENT INSIGHTS
    # =========================
    st.subheader("Content Insights")

    col1, col2 = st.columns(2)

    with col1:
        st.write("### Popularity Distribution")
        st.bar_chart(df['popularity'].value_counts().sort_index())

    with col2:
        explicit_df = df.groupby('is_explicit')['song_id'].nunique()
        st.write("### Explicit vs Clean Songs")
        st.bar_chart(explicit_df)

    st.divider()

    # =========================
    # TREND VIEW
    # =========================
    st.subheader("Chart Trends")

    trend = df.groupby(['date'])['position'].mean()
    st.line_chart(trend)

else:
    st.info("Upload your CSV file to begin")
