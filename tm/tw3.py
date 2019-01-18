# coding: utf-8
from requests_oauthlib import OAuth1Session
from requests.exceptions import ConnectionError, ReadTimeout, SSLError
import json, datetime, time, pytz, re, sys, traceback, pymongo
from pymongo import MongoClient
from collections import defaultdict
from pprint import pprint
import numpy as np
import unicodedata
import MeCab as mc
import collections
import json

KEYS = {
    'consumer_key': 'U6OCU525mGe27DntCYQnIlp70',
    'consumer_secret': 'mZeQ8HdILVbnZB3lRQJht1T8gB7yKmQMnJkkUMLGoLtDHvr6Qn',
    'access_token': '875272026281332737-nrx6TzruwZs7Pge90SXaAD89bxAbRoF',
    'access_secret': 'wxSlu6NaXEhYpst7SeHL2fJLAh0a5McWzfL0zq6LLTbWg'
}

twitter = None
connect = None
db      = None
tweetdata = None
meta    = None

freqwords = {}
freqpair = {}
max = 0

noun_score = 0
verb_score = 0
adjective_score = 0
noun_score_c, adjective_score_c, verb_score_c, adverb_score_c = 0, 0, 0, 0

# TwitterAPI, MongoDBへの接続設定
def initialize():
    global twitter, connect, db, tweetdata, meta
    twitter = OAuth1Session(KEYS['consumer_key'], KEYS['consumer_secret'],
                            KEYS['access_token'], KEYS['access_secret'])
    connect = MongoClient('localhost', 27017)
    db      = connect.okymrestaurant
    #db      = connect.anal1
    tweetdata = db.tweetdata
    meta    = db.metadata

initialize()

# 感情辞書によるポジネガ分析の前段処理
noun_words, adjective_words, verb_words, adverb_words = [], [], [], []
noun_point, adjective_point, verb_point, adverb_point = [], [], [], []

pn = open('/home/odalab/Desktop/kankou/tm/pn_corpus/pn_ja.dic.txt', 'r')

positive_weight = 44861.0 / 49963.0 #1.0
negative_weight = 5122.0 / 49983.0

for line in pn:
   line = line.rstrip()
   x = line.split(':')
   if abs(float(x[3])) > 0: #ポイントの調整
      if x[2] == '名詞':
         noun_words.append(x[0])
         noun_point.append(x[3])
      if x[2] == '形容詞':
         adjective_words.append(x[0])
         adjective_point.append(x[3])
      if x[2] == '動詞':
         verb_words.append(x[0])
         verb_point.append(x[3])
      if x[2] == '副詞':
         adverb_words.append(x[0])
         adverb_point.append(x[3])
pn.close()

# tweet検索
def getTweetData(search_word):
    global twitter
    url    = 'https://api.twitter.com/1.1/search/tweets.json'
    params = {
        'q': search_word, 
        'count': '100'
    }

    req = twitter.get(url, params = params)

    if req.status_code == 200:
        # 成功
        timeline = json.loads(req.text)
        metadata = timeline['search_metadata']
        statuses = timeline['statuses']
        limit    = req.headers['x-rate-limit-remaining'] if 'x-rate-limit-remaining' in req.headers else 0
        reset    = req.headers['x-rate-limit-reset'] if 'x-rate-limit-reset' in req.headers else 0
        return {
            "result": True,
            "metadata": metadata,
            "statuses": statuses,
            "limit": limit,
            "reset_time": datetime.datetime.fromtimestamp(float(reset)),
            "reset_time_unix": reset
        }
    else:
        # 失敗
        return {
            "result": False,
            "status_code": req.status_code
        }

# 文字列を日本時間にタイムゾーンを合わせた日付型で返す
def str_to_date_jp(str_date):
    dts = datetime.datetime.strptime(str_date, '%a %b %d %H:%M:%S +0000 %Y')
    return pytz.utc.localize(dts).astimezone(pytz.timezone('Asia/Tokyo'))

# 現在時刻をUNIX時間で返す
def now_unix_time():
    return time.mktime(datetime.datetime.now().timetuple())


#お店情報取得
res = getTweetData(u'岡山市')

if res['result'] == False:
    # 取得に失敗
    print("Error! status code: {0:d}".format(res['status_code']))

if int(res['limit']) == 0:
    # API制限に達した。データはとれてきてる。
    print("API制限に達したっぽい")
else:
    print("API LIMIT:", res['limit'])
    if len(res['statuses']) == 0:
        # 例外投げる 検索結果0件
        pass
    else:
        # mongoDBに入れる
        meta.insert({"metadata": res['metadata'], "insert_date": now_unix_time()})
        for st in res['statuses']:
            tweetdata.insert(st)

def mecab_analysis(sentence):
    t = mc.Tagger('-Ochasen -d /usr/local/lib/mecab/dic/mecab-ipadic-neologd/')
    sentence = sentence.replace('\n', ' ')
    text = sentence.encode('utf-8') 
    node = t.parseToNode(text)
    result_dict = defaultdict(list)
    for i in range(140):  # ツイートなのでMAX140文字
        if node.surface != "":  # ヘッダとフッタを除外
            word_type = node.feature.split(",")[0]
            if word_type in ["名詞", "形容詞", "動詞"]:
                plain_word = node.feature.split(",")[6]
                if plain_word != "*":
                    result_dict[word_type.decode('utf-8')].append(plain_word.decode('utf-8'))
        node = node.next
        if node is None:
            break
    return result_dict

all_words_list = []

#全てのTweetデータに対して形態素に分けていく処理
for d in tweetdata.find({},{'_id':1, 'id':1, 'text':1, 'noun':1, 'verb':1, 'adjective':1}, no_cursor_timeout=True, timeout=False):
    freqwords = {}
    freqpair = {}
    max = 0

    res = mecab_analysis(unicodedata.normalize('NFKC', d['text'])) # 半角カナを全角カナに

    words_list = []
    hozon_list = {}
    freqp_word = []

    # 品詞毎にフィールド分けして入れ込んでいく
    # 単語出現回数をカウント
    for k in res.keys():
        if k == u'形容詞': # adjective  
            adjective_list = []
            for w in res[k]:
                words_list.append(w)
                all_words_list.append(w)
                adjective_list.append(w)
                words_cnt = collections.Counter(words_list)
                adjective_cnt = collections.Counter(adjective_list)

                # ポジネガ分析
                s_cnt = 0
                for i in adjective_words:
                    if w == i:
                        if adjective_point[s_cnt] >= 0:
                            adjective_score += float(adjective_point[cnt]) * float(positive_weight)
                            adjective_score_c = float(adjective_point[cnt]) * float(positive_weight)
                        else:
                            adjective_score += float(adjective_point[cnt]) * float(negative_weight)
                            adjective_score_c = float(adjective_point[cnt]) * float(negative_weight)
                    s_cnt += 1
                    #print res[k]
                    #print w, noun_score
                    #print w,i
                    #print "test"
                    #print all_words_list
                print str(w.encode('utf-8')), str(adjective_score)
                hozon_list[w] = {u'単語': words_list, u'品詞': k, u'出現頻度': words_cnt, u'ポジネガ分析結果(総和)': adjective_score, u'ポジネガ分析結果(単体)': adjective_score_c, u'共起頻度': 0}

            tweetdata.update({'_id' : d['_id']},{'$push': {'adjective':{'$each':adjective_list}}})

        elif k == u'動詞': # verb
            verb_list = []
            for w in res[k]:
                words_list.append(w)
                all_words_list.append(w)
                verb_list.append(w)
                words_cnt = collections.Counter(words_list)
                verb_cnt = collections.Counter(verb_list)

                # ポジネガ分析
                s_cnt = 0
                for i in verb_words:
                    if w == i:
                        if verb_point[s_cnt] >= 0:
                            verb_score += float(verb_point[cnt]) * float(positive_weight)
                            verb_score_c = float(verb_point[cnt]) * float(positive_weight)
                        else:
                            verb_score += float(verb_point[cnt]) * float(negative_weight)
                            verb_score_c = float(verb_point[cnt]) * float(negative_weight)
                    s_cnt += 1
                    #print res[k]
                    #print w, noun_score
                    #print w,i
                print str(w.encode('utf-8')), verb_score
                hozon_list[w] = {u'単語': words_list, u'品詞': k, u'出現頻度': words_cnt, u'ポジネガ分析結果(総和)': verb_score, u'ポジネガ分析結果(単体)': verb_score_c, u'共起頻度': 0}

            tweetdata.update({'_id' : d['_id']},{'$push': {'verb':{'$each':verb_list}}})

        elif k == u'名詞': # noun
            noun_list = []
            for w in res[k]:
                words_list.append(w)
                all_words_list.append(w)
                noun_list.append(w)
                words_cnt = collections.Counter(words_list)
                noun_cnt = collections.Counter(noun_list)

                # ポジネガ分析
                s_cnt = 0
                for i in noun_words:
                    if w == i:
                        if noun_point[s_cnt] >= 0:
                            noun_score += float(noun_point[cnt]) * float(positive_weight)
                            noun_score_c = float(noun_point[cnt]) * float(positive_weight)
                        else:
                            noun_score += float(noun_point[cnt]) * float(negative_weight)
                            noun_score_c = float(noun_point[cnt]) * float(negative_weight)
                    s_cnt += 1
                    #print res[k]
                    #print w, noun_score
                    #print w,i
                #no_noun += 1
                print str(w.encode('utf-8')), str(noun_score)
                hozon_list[w] = {u'単語': words_list, u'品詞': k, u'出現頻度': words_cnt, u'ポジネガ分析結果(総和)': noun_score, u'ポジネガ分析結果(単体)': noun_score_c, u'共起頻度': 0}

            tweetdata.update({'_id' : d['_id']},{'$push': {'noun':{'$each':noun_list}}})

        #elif k == u'副詞': # adverb
        #    adverb_list = []
        #    for w in res[k]:
        #        words_list.append(w)
        #        adverb_list.append(w)
        #        words_cnt = collections.Counter(words_list)
        #        adverb_cnt = collections.Counter(adverb_list)

                # ポジネガ分析
        #        s_cnt = 0
        #        for i in noun_words:
        #            if w == i:
        #                if adverb_point[s_cnt] >= 0:
        #                    adverb_score += float(adverb_point[cnt]) * float(positive_weight)
        #                else:
        #                    adverb_score += float(adverb_point[cnt]) * float(negative_weight)
        #            s_cnt += 1
                    #print res[k]
                    #print w, noun_score
        #            print w,i
                #no_noun += 1

        #    tweetdata.update({'_id' : d['_id']},{'$push': {'adverb':{'$each':adverb_list}}})

        # 共起単語出現回数をカウント
        print ("--- 共起頻度 ---")
        for i in range(len(words_list)):
            for j in range(len(freqwords)):
                if words_list[i] == freqwords:
                    freqwords[words_list[i]] += 1
                else:
                    freqwords[words_list[i]] = 1
                if max < freqwords[words_list[i]]:
                    max = freqwords[words_list[i]]

            for j in range(i + 1, len(words_list)):
                if words_list[i] + "\t" + words_list[j] == freqpair:
                    freqpair[words_list[i] + "\t" + words_list[j]] += 1
                    freqp_word.append(freqpair[words_list[i] + "\t" + words_list[j]])
                else:
                    freqpair[words_list[i] + "\t" + words_list[j]] = 1
        hozon_list[words_list[i]] = {u'単語': words_list, u'品詞': k, u'出現頻度': words_cnt, u'ポジネガ分析結果': adjective_score, u'共起頻度': freqp_word}

print max

print("--- 指定した全品詞の出現頻度 ---")
for word, cnt in sorted(words_cnt.iteritems(), key=lambda x: x[1], reverse=True):
    print str(word.encode('utf-8')), cnt
    # JSON化
    print(json.dumps(word,
        indent=4,
        ensure_ascii=False,
        sort_keys=True)),
    print ", ",
    print(json.dumps(cnt,
        indent=4,
        ensure_ascii=False,
        sort_keys=True))
    #f = open('output-okayama.json', 'w')
    #json.dump(word, f, indent=4)

print("--- 名詞の出現頻度 ---")
for word, cnt in sorted(noun_cnt.iteritems(), key=lambda x: x[1], reverse=True):
    print str(word.encode('utf-8')), cnt
    #print(json.dumps(word,
    #    indent=4,
    #    ensure_ascii=False,
    #    sort_keys=True)),
    #print ", ",
    #print(json.dumps(cnt,
    #    indent=4,
    #    ensure_ascii=False,
    #    sort_keys=True))

print("--- 動詞の出現頻度 ---")
for word, cnt in sorted(verb_cnt.iteritems(), key=lambda x: x[1], reverse=True):
    print str(word.encode('utf-8')), cnt
    #print(json.dumps(word,
    #    indent=4,
    #    ensure_ascii=False,
    #    sort_keys=True)),
    #print ", ",
    #print(json.dumps(cnt,
    #    indent=4,
    #    ensure_ascii=False,
    #    sort_keys=True))

print("--- 形容詞の出現頻度 ---")
for word, cnt in sorted(adjective_cnt.iteritems(), key=lambda x: x[1], reverse=True):
    print str(word.encode('utf-8')), cnt
    #print(json.dumps(word,
    #    indent=4,
    #    ensure_ascii=False,
    #    sort_keys=True)),
    #print ", ",
    #print(json.dumps(cnt,
    #    indent=4,
    #    ensure_ascii=False,
    #    sort_keys=True))

#単語出現回数、共起単語出現回数からシンプソン係数を計算 
simp = {}
for key, value in freqpair.iteritems():
    if freqpair[key] == 1:
        continue
        p = re.compile('^([^\t]+)\t([^\t]+)$')
        m = p.search(key)
        if m == None:
            continue
        if freqwords[m.group(1)] < freqwords[m.group(2)]:
            simpson = float(value) / float(freqwords[m.group(1)])
        else:
            simpson = float(value) / float(freqwords[m.group(2)])
        if simpson < 0.1:
            continue
        simp[key] = simpson

    print "%s" % max
    for key, value in freqwords.iteritems():
        print "%s\t%s" % (key, value)
    for key, value in simp.iteritems():
        print "%s\t%s" % (key, value)

f = open('output-okayama.json', 'w')
json.dump(all_words_list, f, indent=4)
f = open('output-okayama-simpson.json', 'w')
json.dump(simp, f, indent=4)
