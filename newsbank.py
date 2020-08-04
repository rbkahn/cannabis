# -*- coding: utf-8 -*-

'''Code for processing newsbank data'''

import pandas as pd
from datetime import date, timedelta
from bs4 import BeautifulSoup
from scrape_utils import process, is_sneaky_duplicate, is_byline
import xml.etree.ElementTree as ET
import os, sys, io
from bs4 import BeautifulSoup


datadir = '../../data'
cleandatadir = './cleaned_data/s'

def get_csv_name(year):
    return 'articles/articles-' + str(year) + '.csv'

def save_csv(df, date):
    df[df['date'].str[:4] == str(date.year)].to_csv(get_csv_name(date.year))

def is_sneaky_duplicate(df, headline, date, first_paragraph):
    return not df.loc[(df['title'] == process(headline)) & (df['date'] == date[:10])].empty and \
        first_paragraph == df.loc[(df['title'] == process(headline)) & \
                                    ((df['date'] ==  date) & \
                                   (df['p#'] == 1.0)), 'text'].values[0]

def clean_newsbank():
    id_set = set()
    article_count = 0
    for year in range(1983,2020):
        our_df = pd.DataFrame(columns=['title', 'date', 'p#', 'text'])
        for article in os.listdir(cleandatadir + str(year)):
            article_path = cleandatadir + '%s/%s' % (year, article)
            with open(article_path, mode='r', encoding='utf-8') as fp:
                try:
                    soup = BeautifulSoup(fp)
                    id = soup.nbx.unq.string
                    if soup.nbx.hed:
                        headline = soup.nbx.hed.string
                    else:
                        headline = "no headline"
                    if id in id_set:
                        articles_skipped += 1
                        print('Already read "%s"' % headline)
                        continue
        
                    # confirm that there is text
                    lead = process(soup.nbx.led.string)
                    if soup.nbx.mnt:
                        main_text = process(soup.nbx.mnt.string)
                    else:
                        main_text = ''
                    if len(lead.split()) < 6 and len(main_text.split()) < 6:
                        print("No text for ", article_path)
                        continue
                    date = soup.nbx.ymd.string
                    paragraph_count = 0 
                    for text in [lead, main_text]:
                        if len(text.split()) >= 6:
                            our_df = our_df.append({'id': id, 
                                'title': process(headline), 
                                'date': date,
                                'p#' : paragraph_count,
                                'text': process(text)}, ignore_index=True)
                            paragraph_count += 1
                    if paragraph_count:
                        id_set.add(id)
                        article_count += 1
                        try:
                            print(article_count, headline, date)
                        except:
                            print(article_count, "trouble printing headline", date)
                except:
                    print("Problem with %s" % article_path)
                    sys.exit()
        our_df.to_csv(get_csv_name(year))


def get_summary():
    l = list()
    for year in range(1980, 2020):
        articles = 0
        tokens = 0
        words = 0
        article_dir = cleandatadir + str(year)
        for filename in os.listdir(article_dir):
            articles += 1
            with open(article_dir + '/' + filename, encoding='utf-8') as f:
                for line in f:
                    words += len(line.split())
        print(year, articles, words)

def get_df(years):
    return pd.concat([pd.read_csv(cleandatadir + str(year)) for year in years], ignore_index=True, sort=False, engine='python')
