# coding: utf-8
import json
from collections import OrderedDict
import pprint
from rdflib import Graph
from rdflib import RDF
import codecs
import sys
import types
import re
import itertools

f = codecs.open('/home/odalab/Desktop/kankou/tm/output-okayama.json', 'r', 'utf-8')
tweet_data = json.load(f)
#print json.dumps(tweet_data, sort_keys = True, indent = 4, ensure_ascii=False)
#tweet_data = json.dumps(tweet_data, sort_keys = True, indent = 4, ensure_ascii=False)
f.close()
#print tweet_data

#restaurant = codecs.open('/home/odalab/Desktop/kankou/lod_data/restaurant.ttl', 'r','utf-8')
restaurant = codecs.open('/home/odalab/Desktop/kankou/lod_data/ra-men.ttl', 'r', 'utf-8')
g = Graph()
g.parse(restaurant, format="n3")
#len(g)

data_restaurant = []
matched_list_decision = []

for stmt in g:
    for i in stmt:
        data_restaurant.append(i.encode('utf-8'))
        td = list(tweet_data)#.encode('utf-8')
        for j in td:
            #print j
            #print j.decode('utf-8')
            pattern = i.encode('utf-8')
            text = j#.decode('utf-8')
            #print pattern, text
            #repatter = re.compile(pattern)
            #matchOB = repatter.match(text)
            #if matchOB:
            #    print matchOB.group()
            #matched_list = re.findall(pattern,text)
            matched_list = re.search(pattern, text)
            #print type(matched_list)
            #print matched_list
            #print matched_list.span()
            #print matched_list.start()
            #print matched_list.end()
            if matched_list is None:
                print "No Matching"
            if not matched_list:
                matched_list_decision.append(text)
                #print matched_list.span()
                #print matched_list.start()
                #print matched_list.end()
                #tmp = {
                #    matched_list_decision: {
                #        "word": matched_list_decision,
                #    }
                #}
                #f2 = open('test2.json', 'w')
                #json.dump(tmp, f2, ensure_ascii=False)
                print text

matched_list_decision = list(itertools.chain.from_iterable(matched_list_decision))
matched_list_decision = set(matched_list_decision)

#print("{}".format(json.dumps(matched_list_decision,indent=4)))
#f = codecs.open('output-okayama-test.json', 'w', 'utf-8')
#json.dump(matched_list_decision, f, indent=4, ensure_ascii=False)

tmp = {
    matched_list_decision: {
        "word": matched_list_decision,
    }
}
f2 = open('test2.json', 'w')
json.dump(tmp, f2, ndent=4, ensure_ascii=False)
