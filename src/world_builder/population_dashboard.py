"""
Basic dashboard for visualizing the results of the rest of the world_builder module.
"""

from typing import List

import streamlit as st
import pandas as pd
import altair as alt


@st.cache
def load_data(path: str = "population.parquet") -> pd.DataFrame:
    """Load data from a Parquet file."""
    return pd.read_parquet(path)


def get_filter_columns(df: pd.DataFrame) -> List[str]:
    """Determine which columns should have filters."""
    return [
        col for col in df.columns if col not in ["first_name", "surname", "chain_code"]
    ]


def apply_filters(df: pd.DataFrame, filter_columns: List[str]) -> pd.DataFrame:
    """Apply sidebar filters for each column in the DataFrame."""
    st.sidebar.header("Filters")
    filtered_df = df.copy()

    for col in filter_columns:
        if df[col].dtype == "object":
            unique_vals = df[col].dropna().unique().tolist()
            selected_vals = st.sidebar.multiselect(
                f"Select {col}", options=unique_vals, default=unique_vals
            )
            filtered_df = filtered_df[filtered_df[col].isin(selected_vals)]
        else:
            min_val = int(df[col].min())
            max_val = int(df[col].max())
            selected_range = st.sidebar.slider(
                f"Select {col} range",
                min_value=min_val,
                max_value=max_val,
                value=(min_val, max_val),
            )
            filtered_df = filtered_df[
                (filtered_df[col] >= selected_range[0])
                & (filtered_df[col] <= selected_range[1])
            ]

    return filtered_df


def plot_distributions(df: pd.DataFrame, col: str):
    """Display bar and pie charts for categorical and numeric data."""
    st.subheader(f"Distribution of {col}")

    if df[col].dtype == "object":
        counts = df[col].value_counts().reset_index()
        counts.columns = [col, "count"]

        bar_chart = (
            alt.Chart(counts)
            .mark_bar()
            .encode(x=alt.X(f"{col}:N", sort="-y"), y="count:Q")
            .properties(width=600)
        )

        pie_chart = (
            alt.Chart(counts)
            .mark_arc(innerRadius=50)
            .encode(
                theta=alt.Theta(field="count", type="quantitative"),
                color=alt.Color(field=col, type="nominal"),
                tooltip=[col, "count"],
            )
            .properties(width=300, height=300)
        )

        st.altair_chart(bar_chart, use_container_width=True)
        st.altair_chart(pie_chart, use_container_width=False)

    else:
        bar_chart = (
            alt.Chart(df)
            .mark_bar()
            .encode(x=alt.X(f"{col}:Q", bin=alt.Bin(maxbins=30)), y="count()")
            .properties(width=600)
        )
        st.altair_chart(bar_chart, use_container_width=True)


def render_dashboard(
    df: pd.DataFrame, filtered_df: pd.DataFrame, filter_columns: List[str]
):
    """Render Streamlit UI elements."""
    st.title("Population Dashboard")

    st.subheader("Filtered Data")
    st.write(filtered_df)

    st.header("Distributions")
    for col in filter_columns:
        plot_distributions(filtered_df, col)


def main():
    df = load_data()
    filter_columns = get_filter_columns(df)
    filtered_df = apply_filters(df, filter_columns)
    render_dashboard(df, filtered_df, filter_columns)


if __name__ == "__main__":
    main()
