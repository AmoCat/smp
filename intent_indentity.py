#!/usr/bin/env python
# coding=utf-8

import re


def hotel_intent(sent):
	return re.search(u"(酒店|宾馆|住宿)", sent) != None

def flight_intent(sent):
	return re.search(u"(航班|机票|飞机|头等舱|经济舱|公务舱)", sent) != None

def train_intent(sent):
	return re.search(u"(火车|动车|高铁|二等座|一等座|硬卧|卧铺|软卧|特等座)", sent) != None

def get_intent(sent):
	sentences = sent.split(u"，")
	print sentences
	intent = []
	for s in sentences:
		if 'flight' not in intent and flight_intent(s):
			print "has intent flight"
			intent.append('flight')
		if 'train' not in intent and train_intent(s):
			print "has intent train"
			intent.append('train')
		if 'hotel' not in intent and hotel_intent(s):
			print "has intent hotel"
			intent.append('hotel')
	return intent
