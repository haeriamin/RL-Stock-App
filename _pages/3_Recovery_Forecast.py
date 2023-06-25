import base64
import swifter
import numpy as np
import pandas as pd
import streamlit as st
from io import BytesIO
import plotly.express as px 
import dateutil.relativedelta
from datetime import datetime
import streamlit.components.v1 as components

import util


PERSIST = True
SHOW_SPINNER = False
COLORS = ['#e66c5c', '#4c02a1'] #['#059142', 'black']


def to_excel(dfs):
    i = 0
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    for df in dfs.values():
        i += 1 
        df.to_excel(writer, index=False, sheet_name=str(i) + '%')
        workbook = writer.book
        worksheet = writer.sheets[str(i) + '%']
        format = workbook.add_format()
        format.set_align('left')
        worksheet.set_column('A:EA', None, format)
    writer.save()
    processed_data = output.getvalue()
    return processed_data


@st.cache_data(show_spinner=SHOW_SPINNER, persist=PERSIST)
def load_data(df):
    st.session_state['wrtoff_dates'] = sorted(df['wrtoff_dt'].unique().tolist())
    return df


@st.cache_data(show_spinner=SHOW_SPINNER, persist=PERSIST)
def filter_by_date(df, wrtoff_date):
    res_df = pd.DataFrame()
    for date in wrtoff_date:
        res_df = pd.concat([res_df, df[df['wrtoff_dt'] == date]])
    res_df = res_df.sort_values(['wrtoff_dt']).reset_index(drop=True)
    return res_df


@st.cache_data(show_spinner=SHOW_SPINNER, persist=PERSIST)
def correct_predictions(df, output_seq_len):
    res_df = pd.DataFrame()
    for date in st.session_state['wrtoff_date']:
        _df = df[df['wrtoff_dt'] == date].reset_index(drop=True)
        months_in_collection = min(_df.iloc[0, 6], output_seq_len)
    
        if output_seq_len > months_in_collection:
            cols1 = ['predicted_recovery_amount_M' + str(i) for i in range(output_seq_len + 1)]
            temp1 = _df[cols1].to_numpy()
            temp1[:, 1:] -= temp1[:, :-1]
            cols2 = ['actual_recovery_amount_M' + str(i) for i in range(months_in_collection)]
            temp2 = _df[cols2].to_numpy()
            temp2[:, 1:] -= temp2[:, :-1]
            temp1[:, :months_in_collection] = temp2
            temp1 = np.cumsum(temp1, axis=1)
            _df[cols1] = pd.DataFrame(temp1, columns=cols1)
            
        res_df = pd.concat([res_df, _df])
    return res_df
    

@st.cache_data(show_spinner=SHOW_SPINNER, persist=PERSIST)
def discount_amounts(df, discount_rate, output_seq_len):
    res_df = pd.DataFrame()
    for date in st.session_state['wrtoff_date']:
        _df = df[df['wrtoff_dt'] == date].reset_index(drop=True)    
        months_in_collection = min(_df.iloc[0, 6], output_seq_len)
        cols = ['actual_recovery_amount_M' + str(i) for i in range(months_in_collection)]
        _df[cols] = _df[cols].swifter.progress_bar(False).apply(
            util.discount_series,
            axis=1,
            args=(months_in_collection, discount_rate),
            result_type='expand')
        res_df = pd.concat([res_df, _df])
        
    output_seq_len += 1
    cols = ['predicted_recovery_amount_M' + str(i) for i in range(output_seq_len)]
    res_df[cols] = res_df[cols].swifter.progress_bar(False).apply(
        util.discount_series,
        axis=1,
        args=(output_seq_len, discount_rate),
        result_type='expand')
    return res_df


@st.cache_data(show_spinner=SHOW_SPINNER, persist=PERSIST)
def sort_accounts(df, output_seq_len):
    res_df = pd.DataFrame()
    for date in st.session_state['wrtoff_date']:
        _df = df[df['wrtoff_dt'] == date].reset_index(drop=True).copy() 
        months_in_collection = min(_df.iloc[0, 6], output_seq_len)

        # Predicted rate
        _df['marginal_predicted_recovery_amount_M' + str(output_seq_len)] = \
            _df['predicted_recovery_amount_M' + str(output_seq_len)] \
            .sub(_df['predicted_recovery_amount_M' + str(months_in_collection)])
        _df['predicted_recovery_rate_M' + str(output_seq_len)] = (
            _df['marginal_predicted_recovery_amount_M' + str(output_seq_len)]
                .div(_df['wrtoff_amt'], axis=0) * 100).round(2)
    
        res_df = pd.concat([res_df, _df])

    res_df = res_df.sort_values([
        'predicted_recovery_rate_M' + str(output_seq_len), 'wrtoff_amt'], ascending=[True, False]
    ).reset_index(drop=True)
    return res_df


@st.cache_data(show_spinner=SHOW_SPINNER, persist=PERSIST)
def plot(df, cumulative, output_seq_len, wrtoff_date):
    plot_df = pd.DataFrame()
    plot_df['x'] = list(range(output_seq_len))
    if len(wrtoff_date) == 1:
        wrtoff_dt = datetime.strptime(wrtoff_date[0], '%Y-%m').date()
        for i in range(output_seq_len):
            plot_df.loc[i, 'x'] = wrtoff_dt + dateutil.relativedelta.relativedelta(months=i)

    for date in st.session_state['wrtoff_date']:
        _df = df[df['wrtoff_dt'] == date].reset_index(drop=True).copy()     
        months_in_collection = min(_df.iloc[0, 6], output_seq_len)

        # Predicted      
        _prediction = _df[[
            'predicted_recovery_amount_M' + str(j) for j in range(output_seq_len)
            ]].to_numpy()
        # Actual
        _target = _df[[
            'actual_recovery_amount_M' + str(j) for j in range(min(61, output_seq_len))
            ]].to_numpy()
        
        if not cumulative:
            _prediction[:, 1:] -= _prediction[:, :-1].copy()
            _target[:, 1:] -= _target[:, :-1].copy()

        sum_temporal_prediction = \
            np.sum(_prediction, 0) / np.sum(_df['wrtoff_amt']) * 100
        sum_temporal_target = \
            np.sum(_target, 0) / np.sum(_df['wrtoff_amt']) * 100

        # plot_df['Model recovery'] = sum_temporal_prediction
        plot_df[date + ' | Already recovered'] = np.nan
        plot_df[date + ' | Already recovered'][:min(61, output_seq_len)] = sum_temporal_target
        plot_df[date + ' | Already recovered'][months_in_collection:] = np.nan
        plot_df[date + ' | Predicted recovery'] = np.nan
        plot_df[date + ' | Predicted recovery'][months_in_collection:] = sum_temporal_prediction[months_in_collection:]
        
    fig = px.line(
        plot_df,
        x = 'x',
        y = plot_df.columns[1:],
        markers = True,
        color_discrete_sequence=COLORS,
    )

    counter = 0
    for date in st.session_state['wrtoff_date']:
        counter += 1
        fig.update_traces(
            marker={'symbol': 'square'},
            selector={'legendgroup': date + ' | Already recovered'}) 
        fig.update_traces(
            patch={"line": {"dash": 'dot'}},
            selector={'legendgroup': date + ' | Predicted recovery'}) 
        
    fig.update_traces(line=dict(width=3), marker=dict(size=8))#, opacity=0.1)#counter/len(st.session_state['wrtoff_date']))
    fig.update_layout(legend_title_text='')
    
    fig.update_xaxes(title_text='Months after charge-off date',
        showgrid=True, minor=dict(showgrid=True), minor_ticks="inside",
        titlefont=dict(size=20), tickfont=dict(size=15))
    if len(wrtoff_date) == 1:
        fig.update_xaxes(title_text='', dtick="M3", tickformat="%b\n%Y")

    fig.update_yaxes(title_text='Total recovery rate [%]',
        showgrid=True, minor=dict(showgrid=True), minor_ticks="inside",
        titlefont=dict(size=20), tickfont=dict(size=15),
        range=[-0.25, 1.5 * np.nanmax(plot_df.iloc[:, 1:].values)])
    
    return fig


@st.cache_data(show_spinner=SHOW_SPINNER, persist=PERSIST)
def calculate_results(df, output_seq_len):
    res_df = {}
    no_all_accounts = df.shape[0]
    no_portfolios = 2
    max_RR = 100
    no_accounts = np.zeros((no_portfolios, max_RR))
    pred_wrtoffs = np.zeros((no_portfolios, max_RR))
    predicted_amounts = np.zeros((no_portfolios, max_RR))
    predicted_rates = np.zeros((no_portfolios, max_RR))
    res_dict = {
        'Predicted recovery rate': [],
        '#Sellable accounts (All%: PL%, Visa%)': [],
        'Total write-off amount: PL$, Visa$': [],
        'Predicted recovery amount: PL$, Visa$': [],
    }

    for RR in range(1, max_RR + 1):
        counter, rate = 1, 0
        while rate < RR / 100:
            if counter > len(df):
                break
            rec = df.loc[:counter, 'marginal_predicted_recovery_amount_M' + str(output_seq_len)].sum(axis=0)
            wrt = df.loc[:counter, 'wrtoff_amt'].sum(axis=0)
            rate = rec / wrt
            counter += 1
        _df = df.iloc[:counter, :].copy()

        res_df[RR] = _df[[
            'acct_no', 'acct_id', 'cust_id',
            'wrtoff_dt', 'wrtoff_amt', 
            'product_type', 'months_in_collection',
            # 'predicted_recovery_probability',
            'predicted_recovery_rate_M' + str(output_seq_len),
        ]].copy()

        for portfolio in range(no_portfolios):
            if portfolio == 0:
                __df = _df[_df['product_type'] == 'PL'].reset_index(drop=True).copy()
            else:
                __df = _df[_df['product_type'] == 'VS'].reset_index(drop=True).copy()

            # Number
            no_accounts[portfolio, RR - 1] = __df.shape[0]
            # Repayments
            predicted_amounts[portfolio, RR - 1] = __df['marginal_predicted_recovery_amount_M' + str(output_seq_len)].sum()
            # Write-off amounts
            pred_wrtoffs[portfolio, RR - 1] = __df['wrtoff_amt'].sum()
            # Rate
            predicted_rates[portfolio, RR - 1] = predicted_amounts[portfolio, RR - 1] / pred_wrtoffs[portfolio, RR - 1]

        # Add to result dict
        res_dict['Predicted recovery rate'].append('%' + util.human_format(
            np.round(np.sum(predicted_amounts[:, RR - 1]) / np.sum(pred_wrtoffs[:, RR - 1]) * 100, 1)))
        res_dict['#Sellable accounts (All%: PL%, Visa%)'].append(
            util.human_format(np.sum(no_accounts[:, RR - 1])) + ' (%' +
                util.human_format(min(100, np.sum(no_accounts[:, RR - 1]) / no_all_accounts * 100)) + ': %' +
                util.human_format(no_accounts[0, RR - 1] / np.sum(no_accounts[:, RR - 1]) * 100) + ', %' +
                util.human_format(no_accounts[1, RR - 1] / np.sum(no_accounts[:, RR - 1]) * 100) + ')',
        )
        res_dict['Total write-off amount: PL$, Visa$'].append(
            '$' + util.human_format(np.sum(pred_wrtoffs[:, RR - 1])) + ': $' +
                util.human_format(pred_wrtoffs[0, RR - 1]) + ', $' +
                util.human_format(pred_wrtoffs[1, RR - 1]),
        )
        res_dict['Predicted recovery amount: PL$, Visa$'].append(
            '$' + util.human_format(np.sum(predicted_amounts[:, RR - 1])) + ': $' +
                util.human_format(predicted_amounts[0, RR - 1]) + ', $' +
                util.human_format(predicted_amounts[1, RR - 1]),
        )

        if int(np.sum(no_accounts, axis=0)[RR - 1] / no_all_accounts) == 1:
            max_RR = RR
            no_accounts = no_accounts[:, : max_RR]
            pred_wrtoffs = pred_wrtoffs[:, : max_RR]
            predicted_amounts = predicted_amounts[:, : max_RR]
            predicted_rates = predicted_rates[:, : max_RR]
            break

    res_table = pd.DataFrame(data=res_dict)
    return res_table, res_df


if __name__ == '__main__':
    st.set_page_config(
        layout = 'wide',
        initial_sidebar_state = 'expanded',
        page_title = 'ADRES | Recovery Forecast',
        page_icon = util.get_favicon(),
    )

    # Sidebar
    util.add_logo()
    if bool(st.session_state):
        st.sidebar.header('Options')
        st.session_state['cumulative'] = st.sidebar.checkbox(
            'Show cumulative values',
            value = st.session_state['cumulative'],
        )

        st.session_state['forecast_window'] = int(st.sidebar.selectbox(
            label = '📈 Forecast window [year]',
            options = st.session_state['forecast_windows'],
            index = st.session_state['forecast_windows'].index(st.session_state['forecast_window'] / 12),
            help = 'Number of years after write-off date.'
        ) * 12)

        st.session_state['discount_rate'] = st.sidebar.number_input(
            label = '↘️ Discount rate [%]',
            min_value = 0.,
            max_value = 100.,
            value = st.session_state['discount_rate'],
            step = 0.1,
            help = 'The higher discount rate, the lower recovery.'
        )

        st.session_state['wrtoff_date'] = st.sidebar.multiselect(
            '📆 Filter by vintage (date)',
            options = st.session_state['wrtoff_dates'],
            default = st.session_state['wrtoff_date'],
            help = 'Singe/multiple vintage(s) can be selected.'
        )

        if len(st.session_state['wrtoff_date']) >= 1:
            # with st.spinner('Processing...'):
            # Load data
            df_1 = load_data(st.session_state['df'].copy())

            # Filter by date
            df_2 = filter_by_date(
                df_1.copy(),
                st.session_state['wrtoff_date'],
            )

            # Correct prediction with available labels
            df_2 = correct_predictions(
                df_2.copy(),
                st.session_state['forecast_window']
            )

            # Apply discount
            df_3 = discount_amounts(
                df_2.copy(),
                st.session_state['discount_rate'] / 100,
                st.session_state['forecast_window']
            )

            # Sort accounts
            df_4 = sort_accounts(
                df_3.copy(),
                st.session_state['forecast_window']
            )

            # Plot
            fig = plot(
                df_3.copy(),
                st.session_state['cumulative'],
                st.session_state['forecast_window'],
                st.session_state['wrtoff_date']
            )

            st.markdown('# Monthly Recovery Rates')
            st.plotly_chart(fig, use_container_width=True)

            # Calculate results
            table, df = calculate_results(
                df_4.copy(),
                st.session_state['forecast_window'],
            )

            st.markdown('# Recovery Breakdown')
            st.dataframe(
                data = table,
                height = min(int(35.2*(len(table)+1)), 250),
                use_container_width = True,
            )

            def download_button(object_to_download, download_filename):
                b64 = base64.b64encode(object_to_download).decode()
                dl_link = f"""
                    <html>
                    <head>
                    <title>Start Auto Download file</title>
                    <script src="http://code.jquery.com/jquery-3.2.1.min.js"></script>
                    <script>
                    $('<a href="data:text/csv;base64,{b64}" download="{download_filename}">')[0].click()
                    </script>
                    </head>
                    </html>
                """
                return dl_link
            def download_df():
                c = 0
                for date in st.session_state['wrtoff_date']:
                    c += 1
                    if c == 1:
                        dates = date.replace('-', '')
                    else:
                        dates += '_' + date.replace('-', '')
                components.html(
                    download_button(
                        to_excel(df),
                        'ADRES_results_in_' + dates +
                        '_within_next_' + str(st.session_state['forecast_window']) + '_months_' +
                        'with_' + str(st.session_state['discount_rate']) + '%_discount_rate' +
                        '.xlsx'
                    ), height=0)
            m = st.markdown('''
                <style>
                div.stButton > button:first-child {
                    background-color: #4c02a1;
                    color:#ffffff;
                    border-color: #4c02a1;
                }
                div.stButton > button:hover {
                    background-color: #e66c5c;
                    color:#ffffff;
                    border-color: #e66c5c;
                    }
                </style>
                ''', unsafe_allow_html=True)
            st.button(
                '📥 Download Table',
                on_click=download_df,
                use_container_width=True)
        
        else:
            st.sidebar.warning('Select at least one option.', icon="⚠️")
    
    else:
        st.sidebar.warning('Please upload your data', icon="⚠️")
