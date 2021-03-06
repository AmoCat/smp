#coding:utf-8

__all__ = ['HotelCommander']

import urllib2
from datetime import datetime, timedelta
import json
import CRFPP
from .retrieval import *
from .ground import date_ground, loc_ground, is_loc_name, price_ground
from .hotel_ground import hotel_ground, type_ground, area_ground
from preprocessor import area_preprocessor
from functools import wraps
import os
import re
from LTP_ne import *
from CH_phonetic import PinYin

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

RESULT_SIZE = 5

SLOTS = ['city', 'area', 'price', 'hotel_level', 'hotel_name', 'check_in_date', 'chek_out_date', 'cost_relative', 'type']

NEEDED_SLOTS = ['city', 'check_in_date'] # 必须的slot

QUESTIONS = {'city': u'您要订哪个城市的酒店呢？',
        'check_in_date': u'您想要哪天入住呢？'} 

REPLY_UNSUPPORTED_START_CITY = u'不支持的城市名'
REPLY_NOT_FOUND = u'没有找到酒店信息'
REPLY_FONFIRM = u""

FILL_DEFAULT_CITY = False #是否填充默认的城市
FILL_DEFAULT_CHECK_IN_DATE = False #是否填充默认的入住日期，默认为今天
FILL_DEFAULT_CHECK_OUT_DATE = False
FILL_CHECK_OUT_DATE = True
FILL_PRICE = True

STATUS_SUCCESS = 0
STATUS_WAITING = 1
STATUS_INTERUPT = 2
STATUS_CONFIRM = 3

MAX_ALIVE_TIME = 10
ORIG_SLOT_NAME_PREFIX = '_'

CONTEXT_EXPECTED = 'expected_slot_name'
CONTEXT_SLOTS = 'slots'

DEBUG = True
#DEBUG = False

HOTEL_TYPICAL_SLOTS = ['price']

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
#MODEL_PATH = os.path.join(DATA_DIR, 'hotel.model') # crf模型路径
MODEL_PATH = os.path.join(DATA_DIR, 'hotel.model') # crf模型路径
tagger = CRFPP.Tagger('-m %s' % (MODEL_PATH))


def cache(func):
    caches = {}

    @wraps(func)
    def wrap(*args):
        if args not in caches:
            caches[args] = func(*args)
        return caches[args]
    return wrap


def make_link(text, link):
    return u"<a href=\"%s\">%s</a>" % (link, text)

class HotelCommander(object):
    def __init__(self):
        #self.tagger = CRFPP.Tagger('-m /Users/Oliver/Documents/IR/笨笨/project/crf.model')
        self.slots = {}
        self.slot_probs = {}
        self.context = {}

    def __orig(self, slot_name):
        '''给定一个slot_name，返回它表示原始数据的keyname'''
        if self.__is_orig(slot_name):
            return slot_name
        return ORIG_SLOT_NAME_PREFIX + slot_name

    def __reg(self, slot_name):
        '''给定一个slot_name，返回它表示规范化后的数据的keyname'''
        if self.__is_orig(slot_name):
            return slot_name[len(ORIG_SLOT_NAME_PREFIX):]
        return slot_name

    def __is_orig(self, slot_name):
        return slot_name.startswith(ORIG_SLOT_NAME_PREFIX)

    def __is_reg(self, slot_name):
        return not self.__is_orig(slot_name)

    '''
    def ltp_process(self, sent):
        url_get_base = "http://ltpapi.voicecloud.cn/analysis/?"
        api_key = 'C2A1p2a08gAyNDgDqktGavGSgQ5ppGxsVONU5G3r'
        format = 'json'
        pattern = 'ner'
        result = urllib2.urlopen("%sapi_key=%s&text=%s&format=%s&pattern=%s" % (url_get_base,api_key,sent.encode('utf-8'),format,pattern))
        content = result.read().strip()
        result = json.loads(content)[0][0]
        words = [r['cont'] for r in result]
        postags = [r['pos'] for r in result]
        nes  = [r['ne'] for r in result]
        return words, postags, nes
    '''

    def ltp_process(self,sent):
        words,pos,nes = LTP_ne(sent)
        return words,pos,nes

    def __is_status_waiting(self):
        r = CONTEXT_EXPECTED in self.context.keys()
        return r

    def get_reply(self, sent, context):
        words, postags, nes = self.ltp_process(sent)
        status, reply, context = self.get_reply_with_lexical(sent, words, postags, nes, context)
        return status, reply, context

    def get_reply_with_lexical(self, sent, words, postags, nes, context):
        '''接口，取得回复。words是unicode'''
        self.context = context
        if not self.__is_status_waiting():
            self.recognize(sent, words, postags, nes)
        else:
            expected_slot_name = self.context.get(CONTEXT_EXPECTED)
            slot = self.recognize_expected_slot(sent, words, postags, nes, expected_slot_name)
            self.slots = self.context.get(CONTEXT_SLOTS, {})
            self.recognize(sent, words, postags, nes)
            if self.__reg(expected_slot_name) in self.slots.keys():
                pass
            elif slot != None:
                self.slots.update(slot)
            else:
                return STATUS_INTERUPT,'',{}
            # 如果没有获得需要的slot，则中断多轮会话

        self.fill_default_slots()
        self.fill_price(sent)
        self.construct_regularize_slots()
        k,v = self.area_recognize(sent)
        self.fill_slot_accord_pre_info()#顺序与前边不可变
        if (k != None) and (v != None):
            self.context['prev'] = (k,v)
        if self.__orig('check_in_date') in self.slots.keys():
            if self.slots[self.__orig('check_in_date')] == u'昨天':
                reply = u'入住日期填写有误'
                return STATUS_SUCCESS,reply,'{}'
        if self.__orig('check_out_date') in self.slots.keys():
            if self.slots[self.__orig('check_out_date')] == u'昨天':
                reply = u'离店日期填写有误'
                return STATUS_SUCCESS,reply,'{}'
        if 'check_in_date' in self.slots.keys() and 'check_out_date' in self.slots.keys():
            if self.slots['check_in_date'] == self.slots['check_out_date']:
                reply = u'入住日期与离店日期不能相同'
                return STATUS_SUCCESS, reply, '{}'
        if 'check_in_date' in self.slots.keys():
            self.fill_check_out_time(self.slots['check_in_date'])
        status, reply, context = self.construct_reply()
        return status, reply, context

    def fill_slot_accord_pre_info(self):
        '''
        对本次识别到的slot，加入到pre_info
        '''
        for k,v in self.slots.items():
            k = self.__reg(k)
            if k not in self.context['pre_info'] or \
                (k in self.context['pre_info'] and k in self.slots and self.context['pre_info'][k] != self.slots[k]):
                if k == 'price' and not self.slots[k].has_key('num'):
                    continue
                self.context['pre_info'][k] = (self.slots[k], MAX_ALIVE_TIME)

        if self.context.has_key('pre_info'):
            for k,v in self.context['pre_info'].items():
                if not self.slots.has_key(k):
                    self.slots[k] = v[0]
                t0 = self.context['pre_info'][k][0]
                tmp = self.context['pre_info'][k][1]
                self.context['pre_info'][k] =  (t0,tmp -  1)
                if k == 'arrival_city':
                    self.slots['city'] = v[0]
                if k == 'start_date':
                    self.slots['check_in_date'] = v[0]
                if self.context['pre_info'][k][1] == 0:
                    self.context['pre_info'].pop(k)


    def fill_price(self, sent):
        if self.slots.has_key('price'):
            return
        price = price_ground(sent)
        if price:
            self.slots['price'] = price
            #self.context['pre_info']['hotel_price'] = (price, MAX_ALIVE_TIME-1)

    def add_slot(self, slot_name, slot_value, prob):
        if slot_name not in self.slots:
            self.slots[slot_name] = slot_value
            self.slot_probs[slot_name] = prob
        elif slot_name in self.slot_probs.keys():
            if prob > self.slot_probs[slot_name]:
                self.slots[slot_name] = slot_value
                self.slot_probs[slot_name] = prob
        elif slot_name in self.slots:
            '''waiting状态重新输入'''
            self.slots[slot_name] = slot_value
            self.slot_probs[slot_name] = prob

    def recognize_expected_slot(self, sent, words, postags, nes, expected_slot_name):
        '''单个词CRF不能识别，在此处先根据标准化来判断是否为所需回答'''
        if expected_slot_name not in SLOTS:
            return None
        regularized_slot_value = self.regularize_slot(expected_slot_name,sent)
        if regularized_slot_value != None:
            return {self.__orig(expected_slot_name):sent}
        return None

    def loc_name(self, sent):
        res = is_loc_name(sent,default= None)
        return res

    def area_recognize(self, sent):
        if 'city' in self.slots:
            k, v = area_preprocessor(sent, self.slots['city'])
        else:
            k, v = area_preprocessor(sent)
        if v == None:
            return None, None
        self.slots['area'] = k.decode('utf-8')
        if len(v) == 1:
            self.slots['area'] = k.decode('utf-8')
            if 'city' not in self.slots:
                self.slots['city'] = v[0][1].decode('utf-8')
        else:
            return k.decode('utf-8'), [t[1].decode('utf-8') for t in v]
        return None,None

    def recognize(self, sent, words, postags, nes):
        '''识别slot'''
        if self.loc_name(sent):
            return
        tagger.clear()
        size = len(words)
        for i in range(size):
            cont = ' '.join([words[i], postags[i], nes[i]])
            tagger.add(cont.encode('utf-8'))
        tagger.parse()

        word = ''
        cur_slot_name = ''
        prob = 0
        for i in range(size):
            tag = tagger.y2(i)
            #print "#########"+tag, tagger.prob(i)
            if tag.startswith('B-'):
                if word:
                    self.add_slot(self.__orig(cur_slot_name), word, prob)
                    print "###cur_slot_name = ",cur_slot_name
                    #slots[self.__orig(cur_slot_name)] = word
                    word, cur_slot_name = '', ''
                    prob = 0
                word += words[i]
                cur_slot_name = tagger.y2(i)[2:]
                prob = tagger.prob(i)
            elif tag.startswith('I-'):
                word += words[i]
            elif tag == 'O':
                if word:
                    self.add_slot(self.__orig(cur_slot_name), word, prob)
                    #slots[self.__orig(cur_slot_name)] = word
                    word, cur_slot_name = '', ''
                    prob = 0
        if word:
            #slots[self.__orig(cur_slot_name)] = word
            self.add_slot(self.__orig(cur_slot_name), word, prob)

    def construct_regularize_slots(self):
        '''把slots中未规范化的slot规范化'''
        print "###",self.slots
        for k, v in self.slots.items():
            print "### k = ",k,"v = ",v
            if self.__is_reg(k): ## 如果不是待规范的slot_name，则跳过
                continue
            if self.__reg(k) in self.slots: ## slots里面已经存在规范化过的了
                continue
            regularized_slot_value = self.regularize_slot(k, v)
            print "###regularized_slot_value =",regularized_slot_value 
            if regularized_slot_value != None:
                if(self.context['pre_info'].has_key(self.__reg(k))):
                        self.context['pre_info'][self.__reg(k)] = (regularized_slot_value, MAX_ALIVE_TIME - 1)
                self.slots[self.__reg(k)] = regularized_slot_value
        #print "###construct_regularize_slots",self.slots

    def regularize_slot(self, slot_name, slot_value):
        '''规范化slot'''
        slot_name = self.__reg(slot_name)
        r = slot_value
        if slot_name in ['city']:
            r = self.regularize_loc(slot_value)
        elif slot_name in ['check_in_date', 'check_out_date']:
            r = self.regularize_date(slot_value)
        elif slot_name == 'cost_relative':
            r = slot_value
        elif slot_name == 'hotel_name':
            r = self.regularize_hotel(slot_value)
        elif slot_name == 'type':
            r = self.regularize_type(slot_value)
        elif slot_name == 'area' and self.__orig('city') in  self.slots:
            r,_ = self.regularize_area(slot_value)
        return r

    def regularize_area(self, area):
        k,r = area_ground(area, self.slots[self.__orig('city')])
        return k,r[0][0]

    def regularize_loc(self, loc):
        r = loc_ground(loc, default = None)
        return r

    def regularize_hotel(self, hotel):
        r = hotel_ground(hotel, default = None)
        return r

    def regularize_type(self, h_type):
        r = type_ground(h_type, default = None)
        return r

    def regularize_date(self, dt):
        today = datetime.today()
        tomorrow = today + timedelta(days=1)
        d = date_ground(dt, today, default=None)
        r = '%d-%02d-%02d' % (d.year, d.month, d.day) if d else None
        return r

    def fill_check_out_time(self,dt):
        if FILL_CHECK_OUT_DATE:
            if 'check_in_date' in self.slots and 'check_out_date' not in self.slots:
                today = datetime.today()
                d = date_ground(dt, today, default=None)
                if d!=None:
                    d = d + timedelta(days=1)
                    r = '%d-%02d-%02d' % (d.year, d.month, d.day)
                    self.slots[self.__reg('check_out_date')] = r

    def fill_default_slots(self):
        if FILL_DEFAULT_CITY and 'city' not in self.slots:
            pass
        if FILL_DEFAULT_CHECK_IN_DATE and 'check_in_date' not in self.slots:
            today = datetime.now()
            self.slots.update({'check_in_date': '%d-%02d-%02d' % (today.year, today.month, today.day)})
        if FILL_DEFAULT_CHECK_OUT_DATE and 'check_out_date' not in self.slots:
            tomorrow = datetime.now()+timedelta(days=1)
            self.slots.update({'start_date': '%d-%02d-%02d' % (tomorrow.year, tomorrow.month, tomorrow.day)})

    def construct_reply(self):
        '''构造回复'''
        #不支持的地点
        if self.__orig('city') in self.slots and 'city' not in self.slots:
            reply = REPLY_UNSUPPORTED_START_CITY
            context = {}
            if DEBUG:
                context = {CONTEXT_SLOTS: self.slots}
            return STATUS_SUCCESS, reply, context

        # 是否缺少必须的slot
        for needed_slot_name in NEEDED_SLOTS:
            if needed_slot_name not in self.slots:
                reply = self.get_question(needed_slot_name)
                if self.context.has_key('prev') and needed_slot_name == 'city':
                    reply_pre = self.get_prev_city(self.context['prev'])
                    reply = reply_pre + reply
                self.context[CONTEXT_EXPECTED] = needed_slot_name
                self.context[CONTEXT_SLOTS] = self.slots
                return STATUS_WAITING, reply.encode('utf-8'), self.context

        # 如果必须的slot都有了
        # 若之前完成过意图且有更精确的筛选范围
        if self.context.has_key('last_finish_intent') and self.context['last_finish_intent'] == "hotel":
            for k in TRAIN_TYPICAL_SLOTS:
                if k not in self.slots and k in self.context['last_finish_slot']:
                    #reply = self.get_confirm_question(self.slots)
                    #self.context['confirm_slot'] = self.context['last_finish_slot'][k]
                    #self.context[CONTEXT_SLOTS] = self.slots
                    #return STATUS_CONFIRM, reply.encode('utf-8'), self.context
                    self.slots[k] = self.context['last_finish_slot'][k]

        info = self.get_hotel_info(self.slots)
        if info['status'] == 1:
            hotels = info['hotels']
            reply = self.make_reply_title(self.slots['check_in_date'],
                    self.slots['check_out_date'],self.slots['city'],0)
            if len(hotels) == 0:
                reply = self.make_reply_title(self.slots['check_in_date'],
                    self.slots['check_out_date'],self.slots['city'],1)
                context = {}
                if DEBUG:
                    context = {CONTEXT_SLOTS: self.slots}
                return STATUS_SUCCESS, reply.encode('utf-8'), context
            if self.slots.has_key('price') and self.slots['price'].has_key('cheaper'):
                reply[len(reply)-2] = u","
                reply += u"其中较便宜的" + str(RESULT_SIZE) + "信息如下:\n"
                hotels.sort(key=lambda x: int(x.price))
            if len(hotels) != 0:
                reply += '\n'+'\n'.join([str(f) for f in hotels[:RESULT_SIZE]]).decode('utf-8')
                reply += '\n'
            else:
                #reply = u"\"
                reply +=u'\n没有符合条件的酒店信息\n'
        elif info['status']==2:
            reply = REPLY_UNSUPPORTED_START_CITY
        else:
            reply = REPLY_NOT_FOUND
        context = {}
        if DEBUG:
            #context = {CONTEXT_SLOTS: self.slots}
            context = self.context
            context[CONTEXT_SLOTS] = self.slots
        return STATUS_SUCCESS, reply.encode('utf-8'), context

    def hash_time(self, str):
        l = str.split(':')
        h = int(l[0])
        m = int(l[1])
        return h*60+m


    def make_reply_title(self, check_in_date, check_out_date, city, type):
        year, month, day = check_in_date.split('-')
        month = month.lstrip('0')
        day = day.lstrip('0')
        if type == 0:
            return u"以下是我找到的%s月%s日%s地区的酒店信息" % (month, day, city)
        else:
            return u"帮您找到了%s月%s日%s地区的酒店信息:" % (month, day, city)

    def get_hotel_info(self, slots):
        retrieval = HotelRetrieval(slots)
        info = retrieval.retrieval()
        return info

    def get_question(self, slot_name):
        return QUESTIONS[slot_name]

    def get_prev_city(self, t):
        res = u','.join(t[1])
        res += u"都有" + t[0] + u','
        return res

