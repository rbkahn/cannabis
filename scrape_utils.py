'''helper functions for scraping NYT articles'''

import pandas as pd
import os, sys
from datetime import date

def is_sneaky_duplicate(df, article, first_paragraph):
    return not df.loc[(df['title'] == process(article.headline['main'])) & (df['date'] == article.pub_date[:10])].empty and \
        first_paragraph == df.loc[(df['title'] == process(article.headline['main'])) & \
                                    ((df['date'] ==  article.pub_date[:10]) & \
                                   (df['p#'] == 1.0)), 'text'].values[0]
def is_byline(paragraph):
    return (len(paragraph.split()) < 11 and paragraph[:12] == 'Compiled by ') or \
            (len(paragraph.split()) < 10 and paragraph[:3] == 'By ')


def process(text):
    text = text.replace("\n", "")
    text = ' '.join(text.split())
    return text

def get_df(years=None):
    if not years:
        return pd.concat([pd.read_csv('articles/' + file) for file in os.listdir('articles') if 'articles' in file], ignore_index=True, sort=False)
    else:
        return pd.concat([pd.read_csv(get_csv_name(year)) for year in years], ignore_index=True, sort=False)

def get_csv_name(year):
    return 'articles/articles-' + str(year) + '.csv'

def save_csv(df, date):
    df[df['date'].str[:4] == str(date.year)].to_csv(get_csv_name(date.year))
    with open('last_date.txt', 'w') as f: 
        f.write(str(date)) 

def clean_data(df):
    df['date'] = df['date'].apply(lambda x : x[:10])
    df.drop([col for col in df.columns if 'Unnamed' in col], axis=1, inplace=True)
    print("Original shape: ", df.shape)
    df.drop(df.loc[df['text'] == "We’re sorry, we seem to have lost this page, but we don’t want to lose you."].index, inplace=True)
    df.drop(df.loc[df['text'] == "We’re sorry, we seem to have lost this page, but we don’t want to lose you. Report the broken link here."].index, inplace=True)
    df.drop(df.loc[df['text'] == "Go to Home Page »"].index, inplace=True)
    print("Dropped failed pages: ", df.shape)
    df.drop(df.loc[(df['text'].str.startswith('Compiled by ')) & (df['p#'] == 1.0)].index, inplace=True)
    df.drop(df.loc[(df['text'].str.startswith('By ')) & (df['p#'] == 1.0)].index, inplace=True)
    print("Dropped byline paragraphs: ", df.shape)
    df['text'] = df['text'].apply(lambda x : x.replace("\n", ""))
    df['text'] = df['text'].apply(lambda x : ' '.join(x.split()))
    df.drop_duplicates(subset=['date', 'title', 'text', 'p#'], inplace=True)
    print("Dropped duplicates: ", df.shape)
    return df
