#!/usr/bin/python
# -*- coding: UTF-8 -*-
import urllib, urllib2
import random
import time
import sys

def LTP_ne(sentence):
    #uri_base = "http://127.0.0.1:12345/ltp"
    uri_base = "http://120.25.81.83:12345/ltp"

    data = {'s': sentence.encode('utf-8'),   'x': 'n',   't': 'ner'}

    request = urllib2.Request(uri_base)
    params = urllib.urlencode(data)
    response = urllib2.urlopen(request, params)
    content = response.read()
    #print content
    dic_data = eval(content)
    data = dic_data[0][0]

    seg_list = []
    pos_list = []
    ner_list = []
    for element in data:
        seg_list.append(element['cont'].decode('utf-8'))
        pos_list.append(element['pos'])
        ner_list.append(element['ne'])

    return seg_list,pos_list,ner_list
   
if __name__ == "__main__":
    t = time.time()
    sentences = ['毛泽东是谁','我想去北京天安门','日本的国花是什么','上海的面积是多少','杰克中午吃了十个汉堡','床前明月光','我和你一起去公园']
    for i in range(1):
        seg_list,pos_list,ner_list=LTP_ne(random.choice(sentences))
        print ' '.join(seg_list)
#print len(seg_list)
        print ' '.join(pos_list)
#print len(pos_list)
        print ' '.join(ner_list)
#print len(ner_list)
        print "-------------"
    print time.time()-t
