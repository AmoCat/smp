#coding:utf-8
from datetime import datetime, timedelta
import json
import re
import os
import traceback
import cPickle as pkl

STATION_PATH = os.path.join(os.path.dirname(__file__),'SMPdatabase/station_name.pkl')

stations = pkl.load(open(STATION_PATH, 'r'))

def seats_ground(orig, default = None):
    seats = u"(一等座|二等座|硬座|硬卧|高级软卧上铺|软卧上铺|软卧|特等座)"
    f = re.findall(seats, orig)
    if f:
        return f
    return default

def station_ground(orig, default = None):
    to = u"(去|到|往|去往|出发|开往)"
    res = {}
    for s in stations:
        if s in orig:
            if re.search(s + to, orig):
                res['originStation'] = s
            if re.search(to + s, orig):
                re['terminalStation'] = s
    if res.has_key('originStation') or res.has_key('terminalStation'):
        return res
    return default

def type_ground(orig, default = None):
    #type_dic = {u'动车':u'动车组',u'高铁':u'高速动车',u'特快':u'空调特快',u'直达':u'直达特快'}
    type_dic = {u'动车':u'D',u'高铁':u'G',u'特快':u'T',u'直达':u'Z'}
    for k,v in type_dic.items():
        if k in orig:
            return v
    t_dic = {u'快':u'K'}
    for k,v in t_dic.items():
        if k in orig:
            return v
    return orig


def trainnum_ground(orig, default = None):
    orig = orig.replace('特快','T')
    orig = orig.replace('快','K')
    orig = orig.replace('直达','Z')
    orig = orig.replace('高铁','G')
    orig = orig.replace('动车','D')
    return orig