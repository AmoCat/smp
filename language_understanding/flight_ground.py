# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import json
import re
import os
import traceback

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
AIRPORT_MAP_PATH = os.path.join(DATA_DIR, 'china_airports.txt')
AIRLINE_NAME = os.path.join(os.path.dirname(__file__),'SMPdatabase/airline_name.txt')
#AIRLINE_PATH = os.path.join(DATA_DIR,'china_airline.txt')

airport_map = json.load(open(AIRPORT_MAP_PATH))
#airline_map = json.load(open(AIRLINE_PATH))



def airport_ground(orig, default=None):
    orig = orig.replace("国际机场".decode("utf-8"),"".decode("utf-8"))
    orig = orig.replace("飞机场".decode("utf-8"),"".decode("utf-8"))
    for k,v in airport_map.items():
        if orig in v:
            res = v.replace(u"机场",u"")
            return res
    return orig

def cabin_ground(orig, default = None):
    cabin = u"(经济舱|头等舱|公务舱)"
    c = re.findall(cabin, orig)
    if len(c) > 0:
        return c
    return default

def airline_ground(orig, default = None):
    airlines = eval(open(AIRLINE_NAME, 'r').read().strip())
    tmp = orig.encode('utf-8')
    res = []
    for k,v in airlines.items():
        print tmp,k
        if k in tmp:
            res.append(k.decode('utf-8'))
        for value in v:
            print v
            if value in tmp:
                res.append(k.decode('utf-8'))
    if len(res) > 0:
        return res
    return default

'''
def airline_ground(orig, default = None):
    orig = orig.replace("航空公司".decode("utf-8"),"".decode("utf-8"))
    for k,v in airline_map.items():
        if orig in k or orig == v:
            return v
    return default
'''

def get_loc(orig, default=None):
    for k,v in airport_map.items():
        if orig in v:
            if k == u'北京1':
                k = u'北京'
            if k == u'上海1':
                k = u'上海'
            return k,v
    return default,default