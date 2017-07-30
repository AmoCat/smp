#!/usr/bin/env python
# coding=utf-8
import os

from ground import price_ground, rate_ground
from .flight_ground import airline_ground
from .train_ground import type_ground, station_ground, seats_ground
from LTP_ne import *
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
FLIGHT_MODEL_PATH = os.path.join(DATA_DIR, 'flight.model')
TRAIN_MODEL_PATH = os.path.join(DATA_DIR, 'train.model')

def deletePrice(slots, cur):
	p = float(slots['price']['num'][0])
	cur_p = float(cur)
	if slots['price']['relative'] == 'less' and cur_p <= p:
		return 0
	elif slots['price']['relative'] == 'more' and cur_p >= p:
		return 0
	elif slots['price']['relative'] == 'between':
		r_p = float(slots['price']['num'][1])
		if cur_p >= p and cur_p <= r_p:
			return 0
		else:
			return 1
	else:
		return 1

def detect_price_change(sent):
	p = price_ground(sent)
	return p

def detect_f_change(sent):
	r = rate_ground
	airline = airline_ground
	if r and air:
		return r and air
	else:
		word, pos, ner = LTP_ne(sent)
		tagger = CRFPP.Tagger('-m %s' % (FLIGHT_MODEL_PATH))
		recog = recognize(sent, words, postags, nes, tagger)
		return recog

def detect_t_change(sent):
	t = type_ground(sent)
	s = seats_ground(sent)
	sta = station_ground(sent)
	if not (t and s and sta):
		word, pos, ner = LTP_ne(sent)
		tagger = CRFPP.Tagger('-m %s' % (TRAIN_MODEL_PATH))
		recog = recognize(sent, words, postags, nes, tagger)
		return recog
	return None

def recognize(self, sent, words, postags, nes, tagger):
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
        if tag.startswith('B-'):
    		if word and cur_slot_name != 'cost_relative':
        		return True
        		word, cur_slot_name = '', ''
        		prob = 0
   			word += words[i]
    		cur_slot_name = tagger.y2(i)[2:]
    		prob = tagger.prob(i)
        elif tag.startswith('I-'):
    		word += words[i]
        elif tag == 'O':
    		if word and cur_slot_name != 'cost_relative':
        		return True
        		word, cur_slot_name = '', ''
        		prob = 0
    if word and cur_slot_name != 'cost_relative':
        return True
    return False