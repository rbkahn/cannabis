import pandas as pd

df = pd.read_csv('articles.csv')
df['date'] = pd.to_datetime(df['date'])
min = 1980
max = 2020
step = 1
for year in range(min, max, step):
    dec_df = df[(pd.to_datetime(df['date']).dt.year >= year) & (pd.to_datetime(df['date']).dt.year < (year + step))]
    dec_df.to_csv('articles/%d-%d.csv' % (year, year+step))
    