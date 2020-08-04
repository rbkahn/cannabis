#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
from collections import defaultdict, Counter
import csv, string
from gensim.similarities.index import AnnoyIndexer
from gensim.models import Word2Vec, KeyedVectors
from mittens import Mittens
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
from gensim.parsing.preprocessing import remove_stopwords


def get_csv_name(year):
    return 'articles/articles-' + str(year) + '.csv'

def get_df(years):
    return pd.concat([pd.read_csv(get_csv_name(year)) for year in years], ignore_index=True, sort=False)

def remove_punctuation(p):
    p = p.lower().replace("'s","").replace("’s", "").replace("“", "").replace("”", "")
    return p.translate(str.maketrans('', '', string.punctuation))

def process_paragraphs(df):
    return [remove_waste(p.split()) for p in df['text'].map(remove_punctuation).map(remove_stopwords)]

"""
Removes em-dashes and ampersands from each sentence
"""
def remove_waste(sentence):
    for i in range(len(sentence)):
        if sentence[i][0] == '$':
            sentence[i] = '$'
    wasted_words = ['—', '&']
    return [word for word in sentence if word not in wasted_words]

"""
Generates a co-occurrence matrix from a dataframe of paragraphs. 
Formatted as a dictionary of dictionaries, with outer keys being central
words and inner keys being co-occurring words, linked to their counts.
"""
def co_occurrence(df, window=5, verbose=False, max_vocab=20000):
    if verbose:
        print("co-occurrence")
    sentences = process_paragraphs(df)
    d = dict()
    c = Counter([word for p in sentences for word in p])
    common_words = set(word for word, count in c.most_common()[:max_vocab])
    assert('marijuana' in common_words)
    assert('cannabis' in common_words)
    for sentence in sentences:
        for i in range(len(sentence)):
            if sentence[i] in common_words:
                if sentence[i] not in d:
                    d[sentence[i]] = defaultdict(int)
                for j in range(-window, window):
                    if i+j >= 0 and i+j < len(sentence) and i != j: 
                        d[sentence[i]][sentence[i+j]] += 1
    return d


def d_to_matrix(d):
    print("matrixing")
    vocab = list(d.keys())
    matrix = np.zeros((len(vocab), len(vocab)))
    for i in range(len(vocab)):
        for j in range(len(vocab)):
            matrix[i][j] = d[vocab[i]][vocab[j]]
    return vocab, matrix


def glove2dict(glove_filename):
    with open(glove_filename, encoding="utf8") as f:
        reader = csv.reader(f, delimiter=' ', quoting=csv.QUOTE_NONE)
        embed = {line[0]: np.array(list(map(float, line[1:])))
                for line in reader}
    return embed

def generate_glove(years):
    with open(get_vocab_name(years), "r") as text_file:
        vocab = text_file.readlines()
    for i in range(len(vocab)):
        vocab[i] = vocab[i][:-1]
    co_matrix = np.loadtxt(get_matrix_name(years))
    assert('marijuana' in vocab)
    assert('cannabis' in vocab)
    assert(len(vocab) == co_matrix.shape[0] == co_matrix.shape[1])
    original_embedding = glove2dict('./glove.6B/glove.6B.50d.txt')
    mittens_model = Mittens(n=50, max_iter=1000)
    new_embeddings = mittens_model.fit(co_matrix, vocab=vocab, initial_embedding_dict=original_embedding)
    with open(get_model_name(years, 'glove'), "w", encoding="utf-8") as f:
        f.write('%d 50\n' % len(vocab))
        for i in range(len(vocab)):
            f.write(vocab[i])
            for num in new_embeddings[i]:
                f.write(' %f' % num)
            f.write('\n')
    return new_embeddings, vocab 

def get_sentence_list(years=None, only_weed=False, word_target=None):
    df = get_df(years=years)
    #df['text'] = df['text'].map(process_strings)
    #df['text'] = df['text'].map(remove_stopwords)
    def process_p(p):
        return remove_waste(remove_punctuation(p).split())
    if only_weed:
        if word_target:
            return [p for p in df['text'] if word_target in process_p(p) and ('marijuana' in process_p(p) or 'cannabis' in process_p(p))]
        else:
            return [p for p in df['text'] if 'marijuana' in process_p(p) or 'cannabis' in process_p(p)]
    else:
        if word_target: 
            return [p for p in df['text'] if word_target in process_p(p)]
        else:
            return [p for p in df['text']]

def get_list(years=None, only_weed=False):
    return [item for sublist in get_sentence_list(years, only_weed) for item in sublist]

def generate_w2v(years):
    path = get_model_name(years, 'w2v')
    sentences = get_sentence_list(years=years)
    model = Word2Vec(sentences,min_count=10)
    model.save(path)

def get_model(years, algorithm='glove', with_stopwords=False):
    path = get_model_name(years, algorithm, with_stopwords=with_stopwords)
    if algorithm[0] == 'g' or algorithm[0] == 'n':
        return KeyedVectors.load_word2vec_format(path)
    else:
        return Word2Vec.load(path)

"""
Displays the highlights for the given model.
If instead a list of years is passed, retrieves the model first.
"""
def display_highlights(model, algorithm='glove'):
    if type(model) == range or type(model) == list:
        model = get_model(model, algorithm)
    words = list(model.vocab)
    indexer = AnnoyIndexer(model, 2)
    print(model.most_similar("marijuana", topn=8, indexer=indexer)[1:])
    if algorithm[0] != "n":
        print(model.most_similar("cannabis", topn=8, indexer=indexer)[1:])
    display_closestwords_tsnescatterplot(model, "marijuana")   



def display_closestwords_tsnescatterplot(model, word):
    
    arr = np.empty((0,len(model[word])), dtype='f')
    word_labels = [word]

    # get close words
    close_words = model.similar_by_word(word)
    
    # add the vector for each of the closest words to the array
    arr = np.append(arr, np.array([model[word]]), axis=0)
    for wrd_score in close_words:
        wrd_vector = model[wrd_score[0]]
        word_labels.append(wrd_score[0])
        arr = np.append(arr, np.array([wrd_vector]), axis=0)
        
    # find tsne coords for 2 dimensions
    tsne = TSNE(n_components=2, random_state=0)
    np.set_printoptions(suppress=True)
    Y = tsne.fit_transform(arr)

    x_coords = Y[:, 0]
    y_coords = Y[:, 1]
    # display scatter plot
    plt.scatter(x_coords, y_coords)

    for label, x, y in zip(word_labels, x_coords, y_coords):
        plt.annotate(label, xy=(x, y), xytext=(0, 0), textcoords='offset points')
    plt.xlim(x_coords.min()+0.00005, x_coords.max()+0.00005)
    plt.ylim(y_coords.min()+0.00005, y_coords.max()+0.00005)
    plt.show()

"""generates file name for matrix file for specified years"""
def get_matrix_name(years):
    return "matrix/%d-%d.txt" % (years[0], years[-1])
"""generate file name for vocab file for specified years"""
def get_vocab_name(years):
    return "vocab/%d-%d.txt" % (years[0], years[-1])
"""generate file name for model file for specified years"""
def get_model_name(years, algorithm="glove", with_stopwords=False):
    s = ''
    if algorithm[0] == 'g':
        s = "glove_embeddings/"
    elif algorithm[0] == 'w':
        s = "w2v_embeddings"
    elif algorithm[0] == "n":
        s = "newsbank_embeddings/glove_embeddings/"
    if with_stopwords:
        s += "with_stopwords/"
    return s + "%d-%d.model" % (years[0], years[-1])


"""
Used to generate the co-occurrence matrix for a range of years, specified in the parameter
Saves vocabulary to a txt file with each word on its own line
Saves matrix (np 2darray) as txt file
"""
def generate_matrix(years):
    df = get_df(years)
    co_dict = co_occurrence(df, max_vocab=10000)
    vocab, co_matrix = d_to_matrix(co_dict)
    with open(get_vocab_name(years), 'w', encoding="utf-8") as f:
        f.writelines("%s\n" % word for word in vocab)
    np.savetxt(get_matrix_name(years), co_matrix)

def top_n_df(years, n=10, word='marijuana', with_stopwords=False):
    model = get_model(years, with_stopwords=with_stopwords)
    indexer = AnnoyIndexer(model, 2)
    return pd.DataFrame(model.most_similar(word, topn=n+1, indexer=indexer)[1:], columns=[str(years[0])+'neighbor', 'similarity'+str(years[-1])])

def closest_words(ranges, word="marijuana", n=10, with_stopwords=False):
    if type(ranges) == int:
        d = ranges
        ranges = [range(n, n+d) for n in range(1980, 2020, d)]
    return pd.concat([top_n_df(years, with_stopwords=with_stopwords, word=word, n=n) for years in ranges], axis=1, sort=False)

def get_matrix(years):
    with open(get_vocab_name(years), "r") as text_file:
        vocab = text_file.readlines()
    for i in range(len(vocab)):
        vocab[i] = vocab[i][:-1]
    co_matrix = np.loadtxt(get_matrix_name(years))

def get_vocab(years):
    df = get_df(range(1980, 2020))
    
    