import os
import pandas as pd


def test_msft_csv_columns():
    csv_path = os.path.join('windows_store_apps', 'data', 'msft.csv')
    df = pd.read_csv(csv_path)
    expected_cols = ['Name', 'Rating', 'No of people Rated', 'Category', 'Date', 'Price']
    assert list(df.columns) == expected_cols

