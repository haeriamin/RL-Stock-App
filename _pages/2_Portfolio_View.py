import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px

import util


PERSIST = True
SHOW_SPINNER = False
COLORS = ['#4c02a1', '#e66c5c'] #['#059142', 'black']


@st.cache_data(show_spinner=SHOW_SPINNER, persist=PERSIST)
def load_data(df):
    st.session_state['wrtoff_dates'] = sorted(df['wrtoff_dt'].unique().tolist())
    return df


@st.cache_data(show_spinner=SHOW_SPINNER, persist=PERSIST)
def filter_by_date(df, wrtoff_date):
    res_df = pd.DataFrame()
    for date in wrtoff_date:
        res_df = pd.concat([res_df, df[df['wrtoff_dt'] == date]])
    return res_df


@st.cache_data(show_spinner=SHOW_SPINNER, persist=PERSIST)
def calculate_already_recovered(df):
    res_df = pd.DataFrame()
    for date in st.session_state['wrtoff_date']:
        _df = df[df['wrtoff_dt'] == date].reset_index(drop=True)
        months_in_collection = _df.iloc[0, 6]
        _df['already_recovered_amount'] = _df['actual_recovery_amount_M' + str(months_in_collection)]
        _df['already_recovered_rate'] = \
            _df['already_recovered_amount'].div(_df['wrtoff_amt']) * 100
        res_df = pd.concat([res_df, _df])
    res_df['Portfolio'] = np.where(res_df['acct_no'].str.contains('-'), 'PL', 'Visa')
    return res_df


@st.cache_data(show_spinner=SHOW_SPINNER, persist=PERSIST)
def plot_top(df):
    fig_1 = px.sunburst(
        df,
        path=['Portfolio', 'wrtoff_dt'],
        values='wrtoff_amt',
        title = '',
        color = 'Portfolio',
        color_discrete_sequence = COLORS[::-1],
    )

    fig_2 = px.histogram(
        df,
        x = 'wrtoff_dt',
        y = 'already_recovered_amount',
        color = 'Portfolio',
        color_discrete_sequence = COLORS[::-1],
    )

    fig_1.update_layout(
        font=dict(size=16),
        showlegend=False)
    fig_2.update_layout(
        bargap=0.5,
        legend=dict(font=dict(size= 20)),
        legend_traceorder="reversed")
    fig_2.update_xaxes(
        type='category',
        autorange="reversed",
        title_text='Collection time [month]',
        titlefont=dict(size=20),
        tickfont=dict(size=15))
    fig_2.update_yaxes(
        title_text='Already recovered amount [$]',
        titlefont=dict(size=20),
        tickfont=dict(size=15))

    return fig_1, fig_2


@st.cache_data(show_spinner=SHOW_SPINNER, persist=PERSIST)
def plot_bottom(df):
    fig_1 = px.scatter(
        df,
        x = 'wrtoff_amt',
        y = 'already_recovered_rate',
        size = 'already_recovered_amount',
        color = "Portfolio",
        hover_name = "wrtoff_dt",
        size_max = 100,
        color_discrete_sequence = COLORS[::-1],
    )

    fig_2 = px.density_heatmap(
        df,
        x = "wrtoff_amt",
        y = "predicted_recovery_probability",
        facet_col = "wrtoff_dt",
        nbinsx = 8,
        nbinsy = 8,
        color_continuous_scale = COLORS,
        text_auto = True,
        category_orders = {"wrtoff_dt": sorted(st.session_state['wrtoff_date'])},
    )

    fig_1.update_layout(
        font=dict(size=16),
        showlegend=False)
    fig_1.update_xaxes(
        title_text='Write-off amount [$]',
        titlefont=dict(size=20),
        tickfont=dict(size=15))
    fig_1.update_yaxes(
        title_text='Already recovered rate [%]',
        titlefont=dict(size=20),
        tickfont=dict(size=15))
    fig_2.update_layout(
        legend=dict(font=dict(size= 20)))
    fig_2.update_xaxes(
        title_text='Write-off amount [$]',
        titlefont=dict(size=15),
        tickfont=dict(size=10))
    fig_2.update_yaxes(
        title_text='Recovery probability [%]',
        titlefont=dict(size=20),
        tickfont=dict(size=15))
    fig_2.for_each_annotation(
        lambda a: a.update(text=a.text.split("=")[-1]))

    return fig_1, fig_2


def main():
    df_1 = load_data(st.session_state['df'].copy())

    df_2 = filter_by_date(
        df_1.copy(),
        st.session_state['wrtoff_date']
    )

    df_3 = calculate_already_recovered(
        df_2.copy()
    )

    fig_1, fig_2 = plot_top(
        df_3.copy()
    )

    fig_3, fig_4 = plot_bottom(
        df_3.copy()
    )

    return fig_1, fig_2, fig_3, fig_4


if __name__ == '__main__':
    st.set_page_config(
        layout='wide',
        initial_sidebar_state='expanded',
        page_title='ADRES | Portfolio View',
        page_icon=util.get_favicon(),
    )

    util.add_logo()   
    if bool(st.session_state):
        st.sidebar.header("Options")

        st.session_state['wrtoff_date'] = st.sidebar.multiselect(
            '📆 Filter by vintage (date)',
            options = st.session_state['wrtoff_dates'],
            default = st.session_state['wrtoff_date'],
            help = 'Singe/multiple vintage(s) can be selected.'
        )

        if len(st.session_state['wrtoff_date']) >= 1:
            st.markdown("# Portfolio View")
            fig_1, fig_2, fig_3, fig_4 = main()
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Write-Off Amount Distribution")
                st.plotly_chart(fig_1, use_container_width=True)
            
            with col2:
                st.subheader("Already Recovered Amount Distribution")
                st.plotly_chart(fig_2, use_container_width=True)
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Write-Off Amount vs Already Recovered Rate")
                st.plotly_chart(fig_3, use_container_width=True)
            
            with col2:
                st.subheader("Write-Off Amount vs Recovery Probability")
                st.plotly_chart(fig_4, use_container_width=True)
        
        else:
            st.sidebar.warning('Select at least one option', icon="⚠️")

    else:
        st.sidebar.warning('Please upload your data', icon="⚠️")

