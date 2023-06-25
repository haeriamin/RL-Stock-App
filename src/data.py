import pandas as pd

from src import downloader, preprocessor


def main(stocks, date=None):
    df = downloader.YahooDownloader(
        start_date = date[0],
        end_date = date[1],
        ticker_list = stocks,
    ).fetch_data()
    
    fe = preprocessor.FeatureEngineer(
        use_technical_indicator = True,
        use_turbulence = False,
        user_defined_feature = False,
    )

    df = fe.preprocess_data(df)
    # print(df.head())

    # Add covariance matrix as states
    df = df.sort_values(['date', 'tic'], ignore_index=True)
    df.index = df.date.factorize()[0]

    cov_list = []
    return_list = []

    # Look back is one year
    lookback = len(df.index.unique()) - 2

    for i in range(lookback, len(df.index.unique())):
        data_lookback = df.loc[i - lookback : i, :]
        price_lookback = data_lookback.pivot_table(
            index='date', columns='tic', values='close'
        )
        return_lookback = price_lookback.pct_change().dropna()
        return_list.append(return_lookback)

        covs = return_lookback.cov().values
        cov_list.append(covs)

    df_cov = pd.DataFrame(
        {
            'date': df.date.unique()[lookback:],
            'cov_list': cov_list,
            'return_list': return_list,
        }
    )

    df = df.merge(df_cov, on='date')
    df = df.sort_values(['date', 'tic']).reset_index(drop=True)
    df = preprocessor.data_split(df, date[0], date[1])

    return df
