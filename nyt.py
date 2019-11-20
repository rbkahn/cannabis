import pandas as pd
import requests
import os, sys, signal
from time import sleep
from datetime import date, timedelta
from yanytapi.search import TooManyRequestsException
from bs4 import BeautifulSoup
from yanytapi import SearchAPI
api = SearchAPI("TjGk9kxFO9ScvfSF8AfeqkXjjujBnz6e")

def signal_handler(sig, frame):
    print(str(our_date))
    print(articles_skipped, " articles skipped")
    save_csv(df, our_date.year)
    print('You pressed Ctrl+C!')
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

def is_sneaky_duplicate(df, article):
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


def save_csv(df, year):
    df[pd.to_datetime(df['date']).dt.year == year].to_csv(get_csv_name(year))
    with open('last_date.txt', 'w') as f: 
        f.write(str(our_date)) 

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

articles_skipped = 0
with open('last_date.txt', 'r') as f: 
    date_l = list(map(int, f.read().split('-')))
    our_date = date(date_l[0], date_l[1], date_l[2])
print(our_date)
already_errored = False

df = get_df()
df = clean_data(df)
id_set = set(df['id'])
date_set = set(df['date'])

article_count = 0

while(True):
    if str(our_date) not in date_set:
        for term in ["cannabis", "marijuana"]:
            try: 
                date_str = str(our_date).replace('-', '')
                sleep(6)
                print(term, date_str)
                articles = api.search(term, begin_date=date_str, end_date=date_str)
                
                for article in articles:
                    if article._id in id_set:
                        articles_skipped += 1
                        print('Already read "%s"' % article.headline['main'])
                        continue
                    session = requests
                    url = article.web_url
                    req = session.get(url)
                    soup = BeautifulSoup(req.content, 'html.parser')
                    paragraphs = soup.find_all('p')
                    # Rule out lost pages
                    if "We’re sorry, we seem to have lost this page, but we don’t want to lose you." in paragraphs[0].get_text():
                        print('"'. article.headline['main'], '" is not really retrievable from ', url)
                        id_set.add(article._id)
                        continue
                    # Get rid of bylines
                    first_paragraph = process(paragraphs[0].get_text())
                    if is_byline(first_paragraph):
                        paragraphs = paragraphs[1:]
                        first_paragraph = process(paragraphs[0].get_text())
                    while len(first_paragraph.split()) < 6:
                        paragraphs = paragraphs[1:]
                        first_paragraph = process(paragraphs[0].get_text())
                    # Skip snuck in duplicates
                    if is_sneaky_duplicate(df, article):
                        print('Actually, already read "%s"' % article.headline['main'])
                        articles_skipped += 1
                        id_set.add(article._id)
                        continue
                    paragraph_count = 0
                    for p in paragraphs:
                        text = p.get_text()
                        if len(text.split()) < 6:
                            continue
                        paragraph_count += 1
                        if  process(text) == "Go to Home Page »":
                            continue
                        df = df.append({'id': article._id, 
                                'title': process(article.headline['main']), 
                                'date': article.pub_date[:10],
                                'url': article.web_url,
                                'p#' : paragraph_count,
                                'text': process(text)}, ignore_index=True)
                    if paragraph_count:
                        id_set.add(article._id)
                        article_count += 1
                        print(article_count, article.headline['main'], article.pub_date)
                        if article_count % 50 == 0:
                            save_csv(df, our_date.year)
            except TooManyRequestsException:
                print("Too many requests")
                save_csv(df, our_date.year)
                raise
            except SystemExit:
                raise
            except ConnectionError:
                print("Conection error")
                sleep(6)
                continue
            except StopIteration:
                continue
            except:
                print("Unexpected error:", sys.exc_info())
                if already_errored:
                    print(our_date)
                    print(articles_skipped, " articles skipped")
                    save_csv(df, our_date.year)
                    raise    
                else:
                    already_errored = True
                    continue
    date_set.add(our_date)
    if (our_date.month == 1 and our_date.day == 1):
        article_count = 1
        save_csv(df, our_date.year)
        print("Done with ", our_date.year)
    our_date -= timedelta(days=1)

    already_errored = False