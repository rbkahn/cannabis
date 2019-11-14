import pandas as pd
import pprint
import requests
import os
import sys
import signal
from time import sleep
from datetime import date, timedelta
from yanytapi.search import TooManyRequestsException
from bs4 import BeautifulSoup
from yanytapi import SearchAPI
api = SearchAPI("TjGk9kxFO9ScvfSF8AfeqkXjjujBnz6e")

def signal_handler(sig, frame):
    print(str(date))
    print(articles_skipped, " articles skipped")
    df.to_csv(csv_name)
    print('You pressed Ctrl+C!')
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

def get_csv_name(a_date):
    return 'articles/articles-' + str(a_date.year) + '.csv'

def get_identifier_set(df):
    return set(df['title'] + (pd.to_datetime(df['date']).dt.date).apply(str))
def get_identifier(article):
    return article.headline['main'] + str(pd.to_datetime(article.pub_date)).split(' ')[0]

articles_skipped = 0
with open('last_date.txt', 'r') as f: 
    date_l = list(map(int, f.read().split('-')))
    first_date = date(date_l[0], date_l[1], date_l[2])
#first_date = date.today()
our_date = first_date
already_errored = False

csv_name = get_csv_name(our_date)
if os.path.exists(csv_name):
    df = pd.read_csv(csv_name)
    id_set = set(df['id'])
    check_set = get_identifier_set(df)
    date_set = set(df['date'].apply(lambda x : pd.to_datetime(x).date()))
else:
    df = pd.DataFrame()
    id_set = set()
    check_set = set()
    date_set = set()
article_count = 0

while(True):
    if our_date not in date_set:
        for term in ["cannabis", "marijuana"]:
            try: 
                date_str = str(our_date).replace('-', '')
                print(str(our_date))
                sleep(6)
                articles = api.search(term, begin_date=date_str, end_date=date_str)
                for article in articles:
                    if article._id in id_set or get_identifier(article) in check_set:
                        articles_skipped += 1
                        continue
                    id_set.add(article._id)
                    check_set.add(article.headline['main'] + article.pub_date)
                    article_count += 1
                    print(article_count, article.headline['main'], article.pub_date)
                    session = requests
                    url = article.web_url
                    req = session.get(url)
                    soup = BeautifulSoup(req.content, 'html.parser')
                    paragraphs = soup.find_all('p')
                    count = 0
                    for p in paragraphs:
                        text = p.get_text()
                        if len(text.split()) < 5:
                            continue
                        count += 1
                        df = df.append({'id': article._id, 
                                'title': article.headline['main'], 
                                'date': article.pub_date,
                                'url': article.web_url,
                                'p#' : count,
                                'text': text}, ignore_index=True)
                    if article_count % 50 == 0:
                        df.to_csv(csv_name)
            except TooManyRequestsException:
                print("Too many requests")
                with open('last_date.txt', 'w') as f: 
                    f.write(str(our_date)) 
                raise
            except SystemExit:
                raise
            except ConnectionError:
                print("Conection error")
                sleep(6)
                continue
            except:
                if already_errored:
                    print(our_date)
                    print(articles_skipped, " articles skipped")
                    df.to_csv(csv_name)
                    import sys; print("Unexpected error:", sys.exc_info()[0])
                    raise    
                else:
                    already_errored = True
                    continue
    date_set.add(our_date)
    our_date -= timedelta(days=1)
    if (our_date.month == 1 and our_date.day == 1):
        print("Done with ", our_date.year)
        df.to_csv(csv_name)
        our_date -= timedelta(days=1)
        csv_name = get_csv_name(our_date)
        if os.path.exists(csv_name):
            df = pd.read_csv(csv_name)
            id_set = set(df['id'])
            check_set = get_identifier_set(df)
            date_set = set(df['date'].apply(lambda x : pd.to_datetime(x).date()))
        else:
            df = pd.DataFrame()
            id_set = set()
            check_set = set()
            date_set = set()
        article_count = 0
    already_errored = False

'''
for year in range(2019, 1985, -1):
    if year == 2019:
        sdate = datetime(2019, 11, 1)
    else:
        sdate = datetime(2019, 12, 31)
    csv_name = 'articles-' + str(year) + '.csv'
    if os.path.exists(csv_name):
        df = pd.read_csv(csv_name)
        id_set = set(df['id'])
    else:
        df = pd.DataFrame()
        id_set = set()
    for begin, end in [('0201', '0228'), ('0301', '0331'), ('0401', '0430'), ('0501', '0531'), ('0601', '0630'), ('0701', '0731'), ('0801', '0831'), ('0901', '0930'), ('1001', '1031'), ('1101','1130'), ('1201', '1231'), ('0101', '0131'), ]:
        for term in ["cannabis", "marijuana"]:
            try: 
                begin_date = str(year) + begin
                end_date = str(year) + end
                articles = api.search(term, begin_date=begin_date, end_date=end_date)
                article_count = 0
                for article in articles:
                    if article._id in id_set:
                        articles_skipped += 1
                        continue
                    id_set.add(article._id)
                    article_count += 1
                    print(article_count, article.headline['main'], article.pub_date)
                    session = requests
                    url = article.web_url
                    req = session.get(url)
                    soup = BeautifulSoup(req.content, 'html.parser')
                    paragraphs = soup.find_all('p')
                    count = 0
                    for p in paragraphs:
                        text = p.get_text()
                        if len(text.split()) < 5:
                            continue
                        count += 1
                        df = df.append({'id': article._id, 
                                'title': article.headline['main'], 
                                'date': article.pub_date,
                                'url': article.web_url,
                                'p#' : count,
                                'text': text}, ignore_index=True)
                    
                    if article_count % 50 == 0:
                        df.to_csv(csv_name)
            except:
                print(year, begin, end)
                print(articles_skipped, " articles skipped")
                df.to_csv(csv_name)
                import sys; print("Unexpected error:", sys.exc_info()[0])
                raise
'''
    