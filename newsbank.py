import pandas as pd
from datetime import date, timedelta
from bs4 import BeautifulSoup
from scrape_utils import process, is_sneaky_duplicate, is_byline
import xml.etree.ElementTree as ET


df = pd.DataFrame()
id_set = set(df['id'])

def get_csv_name(year):
    return 'articles/newsbank/articles-' + str(year) + '.csv'

def save_csv(df, date):
    df[df['date'].str[:4] == str(date.year)].to_csv(get_csv_name(date.year))


article_count = 0

for (article in articles)
    tree = ET.parse(article)
    root = tree.getroot()
    id = root.find('UNQ').text
    headline = root.find('HED').text
    if id in id_set:
        articles_skipped += 1
        print('Already read "%s"' % headline)
        continue
    
    # Check for articles that are Sorry we can't find this article
    # Get rid of bylines

    # confirm that there is text
    lead = process(root.find('LED').text)
    first_paragraph = lead
    maintext = process(root.find('MNT').text)
    if is_byline(first_paragraph)
        first_paragraph = maintext
    if len(first_paragraph.split()) < 6:
        print("No text for ", url)
        continue
    # Skip snuck in duplicates
    if is_sneaky_duplicate(df, article, first_paragraph):
        print('Actually, already read "%s"' % headline)
        articles_skipped += 1
        id_set.add(id)
        continue


    date = root.find('YMD').text
    #process lead
    paragraph_count = 0
    for text in [lead, main_text]
        if len(text.split()) >= 6:
            df = df.append({'id': id, 
                    'title': process(headline), 
                    'date': date
                    'p#' : paragraph_count,
                    'text': process(text)}, ignore_index=True)
            paragraph_count += 1
    if paragraph_count:
        id_set.add(id)
        article_count += 1
        print(article_count, headline, date)
    if article_count % 50 == 0:
        save_csv(df, our_date)




'''
import scrapy

class BrickSetSpider(scrapy.Spider):
   name = "brickset_spider"

    #start_urls = ['http://brickset.com/sets/year-2016']
    start_urls = ['https://infoweb-newsbank-com.stanford.idm.oclc.org/apps/news/easy-search?p=AWNB']
    start_urls = ['https://login.stanford.idm.oclc.org/']

    def parse(self, response):
        return scrapy.FormRequest.from_response(
            response,
            formdata={'username': 'rbkahn', 'password': 'applesauce in bourbon'},
            callback=self.after_login
        )
    
    def after_login(self, response):
        self.logger.error(36, response.body)
        if "Error while logging in" in response.body:
            self.logger.error("Login failed!")
        else:
            self.logger.error("Login succeeded!")
            #item = SampleItem()
            #item["quote"] = response.css(".text").extract()
            #item["author"] = response.css(".author").extract()
            return item'''
