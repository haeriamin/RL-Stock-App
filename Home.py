import warnings
import pandas as pd
import streamlit as st
from pytz import timezone
from datetime import datetime
import pandas_market_calendars as mcal

from src import params, predict, train, util


tz = timezone('EST')
warnings.filterwarnings("ignore")


def main():
    st.set_page_config(
        layout='wide',
        initial_sidebar_state='expanded',
        page_title='Home',
        # page_icon=':bank:',
        page_icon=util.get_favicon(),
    )
    st.markdown('# RL Stock App')

    amount_AAPL = st.sidebar.number_input(
        'AAPL share [$]',
        value = 5.,
        step = 0.01
    )
    amount_TSLA = st.sidebar.number_input(
        'TSLA share [$]',
        value = 5.,
        step = 0.01
    )
    commission_perc = st.sidebar.number_input(
        'Commission percentage [%]',
        value = 2.,
        step = 0.01
    )
    initial_amount = amount_AAPL + amount_TSLA
    initial_allocation_1 = amount_AAPL / initial_amount
    initial_allocation_2 = amount_TSLA / initial_amount

    # Get params
    data_params, env_params, model_params, train_params, model_name = params.main()
    
    # Last business dates
    nyse = mcal.get_calendar('NYSE')

    end_date = pd.to_datetime(datetime.now(tz))
    if end_date.hour < 9:
        end_date = end_date - pd.to_timedelta(1, unit='d')

    start_date = end_date - pd.to_timedelta(30, unit='d')
    days = nyse.schedule(start_date=start_date, end_date=end_date)

    length = 4
    start_date = str(days.index[-length])[:10]
    end_date = str(end_date)[:10]
    date = [start_date, end_date]

    # Params
    env_params['initial_amount'] = initial_amount
    env_params['initial_allocation'] = [initial_allocation_1, initial_allocation_2]
    env_params['commission_perc'] = commission_perc

    st.divider()
    st.write(pd.to_datetime(datetime.now(tz)))

    if st.button('Re-train'):
        with st.spinner('Wait for it...'):
            train.main(
                data_params,
                env_params,
                model_params,
                train_params,
                model_name, 
                date
            )
        st.write('Model was re-trained!')

    if st.button('Predict'):
        predict.main(
            data_params,
            env_params,
            model_name,
            date,
        )
    


if __name__ == '__main__':
    main()
