from newspaper import Article
from konlpy.tag import Kkma
from konlpy.tag import Twitter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.preprocessing import normalize
from wordcloud import WordCloud
import stylecloud
import numpy as np
import os


class SentenceTokenizer(object):
    def __init__(self):
        self.kkma = Kkma()
        self.twitter = Twitter()
        self.stopwords = ['중인' ,'만큼', '마찬가지', '꼬집었', "연합뉴스","연합 뉴스", "데일리", "동아일보", "중앙일보", "조선일보", "기자"
                        ,"아", "휴", "아이구", "아이쿠", "아이고", "어", "나", "우리", "저희", "따라", "의해", "을", "를", "에", "의", "가","성모","동아 일보","무단 배포",]

    def url2sentences(self, url):
        article = Article(url, language='ko')
        article.download()
        article.parse()
        sentences = self.kkma.sentences(article.text)

        for idx in range(0, len(sentences)):
            if len(sentences[idx]) <= 10:
                sentences[idx-1] += (' ' + sentences[idx])
                sentences[idx] = ''
        return sentences

    def text2sentences(self, text):
        sentences = self.kkma.sentences(text)
        for idx in range(0, len(sentences)):
            if len(sentences[idx]) <= 10:
                sentences[idx-1] += (' ' + sentences[idx])
                sentences[idx] = ''

        return sentences

    def get_nouns(self, sentences):
        nouns = []
        for sentence in sentences:
            if sentence is not '':
                nouns.append(' '.join([noun for noun in self.twitter.nouns(str(sentence)) if noun not in self.stopwords and len(noun) > 1]))
        print(nouns)
        return nouns


class GraphMatrix(object):
    def __init__(self):
        self.tfidf = TfidfVectorizer()
        self.cnt_vec = CountVectorizer()
        self.graph_sentence = []

    def build_sent_graph(self, sentence):
        tfidf_mat = self.tfidf.fit_transform(sentence).toarray()
        self.graph_sentence = np.dot(tfidf_mat, tfidf_mat.T)
        return self.graph_sentence

    def build_words_graph(self, sentence):
        cnt_vec_mat = normalize(self.cnt_vec.fit_transform(sentence).toarray().astype(float), axis=0)
        vocab = self.cnt_vec.vocabulary_
        return np.dot(cnt_vec_mat.T, cnt_vec_mat), {vocab[word] : word for word in vocab}


class Rank(object):
    def get_ranks(self, graph, d=0.85): # d = damping factor
        A = graph
        matrix_size = A.shape[0]
        for id in range(matrix_size):
            A[id, id] = 0 # diagonal 부분을 0으로
            link_sum = np.sum(A[:,id]) # A[:, id] = A[:][id]
            if link_sum != 0:
                A[:, id] /= link_sum
            A[:, id] *= -d
            A[id, id] = 1
        B = (1-d) * np.ones((matrix_size, 1))
        ranks = np.linalg.solve(A, B) # 연립방정식 Ax = b
        return {idx: r[0] for idx, r in enumerate(ranks)}


class TextRank(object):
    def __init__(self, text):
        self.sent_tokenize = SentenceTokenizer()

        if text[:5] in ('http:', 'https'):
            self.sentences = self.sent_tokenize.url2sentences(text)
        else:
            self.sentences = self.sent_tokenize.text2sentences(text)
        self.nouns = self.sent_tokenize.get_nouns(self.sentences)
        # print('85',self.sentences)
        print('90',self.nouns)

        self.graph_matrix = GraphMatrix()
        self.sent_graph = self.graph_matrix.build_sent_graph(self.nouns)
        self.words_graph, self.idx2word = self.graph_matrix.build_words_graph(self.nouns)
        
        self.rank = Rank()
        self.sent_rank_idx = self.rank.get_ranks(self.sent_graph)
        self.sorted_sent_rank_idx = sorted(self.sent_rank_idx, key=lambda k: self.sent_rank_idx[k], reverse=True)
        self.word_rank_idx = self.rank.get_ranks(self.words_graph)
        self.sorted_word_rank_idx = sorted(self.word_rank_idx, key=lambda k: self.word_rank_idx[k], reverse=True)

    def makewordcloud(self):
        cloud = ''
        print(len(self.nouns))
        for i in self.nouns:
            cloud += i
        print(cloud)
        return cloud

    def summarize(self, sent_num=4):
        summary = []
        index=[]
        for idx in self.sorted_sent_rank_idx[:sent_num]:
            index.append(idx)
        
        index.sort()
        for idx in index:
            if self.sentences[idx] not in summary:
                summary.append(self.sentences[idx])
        
        return summary

    def keywords(self, word_num=10):
        rank = Rank()
        rank_idx = rank.get_ranks(self.words_graph)
        sorted_rank_idx = sorted(rank_idx, key=lambda k: rank_idx[k], reverse=True)

        keywords = []
        index=[]
        for idx in sorted_rank_idx[:word_num]:
            index.append(idx)
        
        #index.sort()
        for idx in index:
            keywords.append(self.idx2word[idx])
        return keywords

def make(text,idx, png_name1, png_name2):
    # wc = WordCloud(font_path='C://windows\\Fonts\\HANYGO230.ttf', \
    #                 # background_color="white",\
    #                 width=1000,\
    #                 height=1000,\
    #                 max_words=100,\
    #                 max_font_size=300)

    # wc.generate(text)
    # wc.to_file(text[1]+'.png')
    try:
        if not os.path.exists("./img/society/"+str(png_name1)):
            os.makedirs("./img/society/"+str(png_name1))
    except:
        pass
    
    try:
        if not os.path.exists("./img/society/"+str(png_name1)+"/"+str(png_name2)):
            os.makedirs("./img/society/"+str(png_name1)+"/"+str(png_name2))
    except:
        pass

    wc = stylecloud.gen_stylecloud(text=text,
                                    icon_name="fab fa-twitter",
                                    font_path='C://windows\\Fonts\\HANYGO230.ttf',
                                    colors=['#032859','#016F94','#FFE4B6','#FFB06D','#FE6A2C','#FCBB6D','#D8737F','#AB6C8C','#685D79','#475C7A'],
                                    palette="colorbrewer.diverging.Spectral_11",
                                    background_color='#EFEFF0',
                                    # gradient="horizontal",
                                    output_name="./img/society/"+str(png_name1)+"/"+str(png_name2)+"/"+str(idx)+".png")

# 출처: https://excelsior-cjh.tistory.com/93 [EXCELSIOR]
# url = 'https://news.naver.com/main/read.nhn?mode=LSD&mid=shm&sid1=105&oid=293&aid=0000033262'

# textrank = TextRank(url)
# for row in textrank.summarize(4):
#     print(row)
#     print()
# print('keywords :',textrank.keywords())