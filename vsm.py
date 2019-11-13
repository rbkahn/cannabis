import pandas as pd
import pprint
import urllib
import requests
pp = pprint.PrettyPrinter(indent=4)
from yanytapi import SearchAPI
from gensim.similarities.index import AnnoyIndexer
from gensim.models import Word2Vec
from mittens import GloVe, Mittens
from gensim.matutils import corpus2csc
from gensim.corpora import Dictionary
from collections import defaultdict
import numpy as np
import pickle
import csv

def process_strings(s):
    s = s.lower().replace(".", "").replace("'s","").replace("?","").replace("!","").replace(",", "").replace(";", "").replace("\"", "").replace("”", "").replace("“", "").replace("(", "").replace(")", "")
    if len(s) > 0 and s[0] == '$':
        return '$'
    return s
    
def csv_name(year):
    return 'articles-' + str(year) + '.csv'

def remove_waste(sentence):
    wasted_words = ['—', '&']
    return [word for word in sentence if word not in wasted_words]

def co_occurrence(df, window=5):
    sentences = [remove_waste(list(map(lambda s : process_strings(s), p.split()))) for p in df['text']]
    d = dict()
    for sentence in sentences:
        for i in range(len(sentence)):
            if sentence[i] not in d:
                d[sentence[i]] = defaultdict(int)
            for j in range(-window, window):
                if i+j >= 0 and i+j < len(sentence) and i != j: 
                    d[sentence[i]][sentence[i+j]] += 1
    return d

def trim_d(d):
    vocab = list(d.keys())
    print(len(vocab))
    for word in d:
        if sum([v for k, v in dict(d[word]).items()]) < 100:
            vocab.remove(word)
    print(len(vocab))
    return {k:v for k, v in d.items() if k in vocab}

def d_to_matrix(d):
    vocab = list(d.keys())
    matrix = np.zeros((len(vocab), len(vocab)))
    for i in range(len(vocab)):
        for j in range(len(vocab)):
            matrix[i][j] = d[vocab[i]][vocab[j]]
    return vocab, matrix

def generate_embeddings(df):
    d = trim_d(co_occurrence(df))
    vocab, cooccurrence = d_to_matrix(d)
    glove_model = GloVe(n=25, max_iter=100)
    embeddings = glove_model.fit(cooccurrence)
    return vocab, embeddings

def glove2dict(glove_filename):
    with open(glove_filename) as f:
        reader = csv.reader(f, delimiter=' ', quoting=csv.QUOTE_NONE)
        embed = {line[0]: np.array(list(map(float, line[1:])))
                for line in reader}
    return embed

df = pd.read_csv('articles-2019.csv')
vocab, cooccurrence = d_to_matrix(trim_d(co_occurrence(df)))
print("Calculated coocurrence")
original_embedding = glove2dict('glove.6B/glove.6B.50d')
print("loaded original embeddings")
mittens_model = Mittens(n=50, max_iter=1000)
# Note: n must match the original embedding dimension
new_embeddings = mittens_model.fit(
    cooccurrence,
    vocab=vocab,
    initial_embedding_dict= original_embedding)
np.savetxt('embeddings.csv', new_embeddings, delimiter=',')
with open("vocab.txt", "wb") as fp:
    pickle.dump(vocab, fp)

'''sentences = [list(map(lambda s : process_strings(s), p.split())) for p in df['text']]
model = Word2Vec(sentences)
print(model)
words = list(model.wv.vocab)
indexer = AnnoyIndexer(model, 2)
print(model.most_similar("marijuana", topn=7, indexer=indexer))
print(model.most_similar("cannabis", topn=7, indexer=indexer))
'''