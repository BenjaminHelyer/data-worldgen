"""Streamlit map and state-level exploration for the US population example."""
import json
import os
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

HERE = Path(__file__).resolve().parent
STATES = pd.DataFrame(json.loads((HERE / 'states.json').read_text()))
# Vega fetches this public TopoJSON in the browser. See README for offline behavior.
TOPOLOGY_URL = 'https://cdn.jsdelivr.net/npm/us-atlas@3/states-10m.json'


def summarize_states(df: pd.DataFrame, profession: str) -> pd.DataFrame:
    """Return one row per state, retaining states with no sampled people."""
    totals = df.groupby('state').size().rename('total')
    selected = df[df['profession'] == profession].groupby('state').size().rename('selected')
    result = STATES[['name', 'abbr', 'fips']].merge(totals, left_on='name', right_index=True, how='left')
    result = result.merge(selected, left_on='name', right_index=True, how='left')
    result[['total', 'selected']] = result[['total', 'selected']].fillna(0).astype(int)
    result['share'] = (result['selected'] / result['total'].replace(0, float('nan')) * 100).round(1)
    return result


def make_map(summary: pd.DataFrame, profession: str) -> alt.Chart:
    geometry = alt.topo_feature(TOPOLOGY_URL, 'states')
    return (alt.Chart(geometry)
        .transform_calculate(state_fips='toNumber(datum.id)')
        .transform_lookup(lookup='state_fips', from_=alt.LookupData(summary, 'fips', ['name', 'total', 'selected', 'share']))
        .transform_filter(alt.datum.name != None)  # 50 states only; excludes DC and territories
        .mark_geoshape(stroke='white', strokeWidth=0.7)
        .encode(
            color=alt.Color('share:Q', title=f'{profession} (%)', scale=alt.Scale(scheme='blues'),
                            legend=alt.Legend(format='.1f')),
            tooltip=[alt.Tooltip('name:N', title='State'), alt.Tooltip('total:Q', title='Sample size'),
                     alt.Tooltip('selected:Q', title=profession),
                     alt.Tooltip('share:Q', title='Share (%)', format='.1f')],
        ).project(type='albersUsa').properties(height=440))


@st.cache_data
def load_population(path: str, modified_ns: int) -> pd.DataFrame:
    del modified_ns
    return pd.read_parquet(path)


def main():
    st.set_page_config(page_title='Synthetic US population', layout='wide')
    st.title('A synthetic working population across the United States')
    st.caption('Illustrative synthetic data, not Census or employment estimates. State population weights are approximate; profession factors are invented.')
    path = Path(os.environ.get('WORLDGEN_US_POPULATION', str(HERE / 'population.parquet'))).expanduser()
    if not path.is_file():
        st.error(f'Population file not found: {path}. Run the generation command in the example README first.')
        st.stop()
    df = load_population(str(path), path.stat().st_mtime_ns)
    if df.empty or not {'state', 'profession'}.issubset(df.columns):
        st.error('The population file must contain at least one row and state and profession columns.')
        st.stop()
    profession = st.selectbox('Color states by profession', sorted(df['profession'].dropna().unique()))
    summary = summarize_states(df, profession)
    st.subheader(f'Share of sampled workers in {profession}')
    st.altair_chart(make_map(summary, profession), use_container_width=True)
    st.caption('Colors show the percentage within each state, not the number of people. Hover for sample sizes. The map requires access to the public us-atlas geometry CDN.')
    state = st.selectbox('Explore a state', STATES['name'].tolist(), index=STATES['name'].tolist().index('Texas'))
    state_df = df[df['state'] == state]
    st.subheader(f'{state}: {len(state_df):,} sampled characters')
    if state_df.empty:
        st.info('No characters were sampled in this state. Generate a larger population to improve coverage.')
        return
    counts = state_df['profession'].value_counts().rename_axis('Profession').reset_index(name='Characters')
    counts['Share (%)'] = (100 * counts['Characters'] / len(state_df)).round(1)
    st.bar_chart(counts.set_index('Profession')['Characters'])
    st.dataframe(counts, hide_index=True, use_container_width=True)
    st.subheader('Sample characters')
    columns = [c for c in ['first_name', 'surname', 'age', 'gender', 'profession', 'character_id'] if c in state_df]
    sample = state_df[columns].sample(n=min(20, len(state_df)), random_state=42).copy()
    if 'age' in sample:
        sample['age'] = sample['age'].round().astype(int)
    st.dataframe(sample, hide_index=True, use_container_width=True)


if __name__ == '__main__':
    main()
