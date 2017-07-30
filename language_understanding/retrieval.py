#!/usr/bin/env python
# coding=utf-8

import os
import sys
import re
from entity import *
from globalCon import MONTH_HASH
import cPickle as pkl
from common import deletePrice

DIR_PATH = os.path.dirname(__file__)

class Retrieval(object):
	'''
	return:
	-1:日期小于2017-04-08
	1:日期大于2017-05-06
	0:二者之间
	'''
	def compare_date(self,date,terminalDay = 16):
		dates = date.split('-')
		month = MONTH_HASH[dates[0]]
		day = int(dates[1][0])*10 + int(dates[1][1])
		if month<4 or (month==4 and day<18):
			return -1
		if month>5 or (month==5 and day>terminalDay):
			return 1
		return 0

	'''
	status:
	0:数据库中没有结果
	1:查到正确结果，进行确认
	2:日期不存在，推荐日期
	3:查询了过去的机票
	4:异常
	'''
	def handle(self,f,file_tail):
		res = {}
		res['status'] = 1

		if f == -1:
			res['status'] = 3
			res['info'] = "不能查询过去日期的机票"
			return res
		elif f == 1:
			res['status'] = 2
			res['info'] = "日期不存在，推荐日期"
			return res
		try:
			datas = open(self.DATABASE_DIR+file_tail,'r')
		except Exception,e:
			print e
			res['status'] = 4
			return res

		lines = datas.read().strip().split('\n')
		datas = []
		for line in lines:
			datas.extend(eval(line.strip()))
		if datas != None:
			tickets = self.search(datas, self.slots, res)
			if len(tickets) == 0:
				res['status'] = 0
			else:
				res['status'] = 1
				res['tickets'] = tickets
		else:
			raise "datas is None!"
		return res

class FlightRetrieval(Retrieval):
	def __init__(self,slots):
		self.slots = slots
		self.DATABASE_DIR = os.path.join(DIR_PATH,"SMPdatabase/flight/")

	def retrieval(self):
		file_tail = self.slots['start_date'][5:]
		f = self.compare_date(file_tail)
		res = self.handle(f, file_tail)
		return res

	'''
	查询时只查出发城市和到达城市符合的
	筛选时间等在外部筛选
	'''
	def search(self, datas, slots, res):
		tickets = []
		for f_ticket in datas:
			#print slots['start_city'].encode('utf-8'),slots['arrival_city'].encode('utf-8')
			#print f_ticket
			if slots['start_city'].encode('utf-8') == f_ticket['departCity'] and\
				slots['arrival_city'].encode('utf-8') == f_ticket['arriveCity']:
				if slots.has_key('price') and slots['price'].has_key('num'):
					if deletePrice(self.slots, f_ticket['price']) != 0:
						continue
				if slots.has_key('rate') and float(slots['rate']) > f_ticket['rate']:
					continue
				if slots.has_key('cabin') and f_ticket['cabinInfo'].decode('utf-8') not in self.slots['cabin']:
					continue
				if slots.has_key('rate') and float(slots['rate']) < float(f_ticket['rate']):
					continue
				if slots.has_key('airline') and f_ticket['airline'].decode('utf-8') not in slots['airline']:
					continue
				tickets.append(FlightTicket(f_ticket))
		return tickets


class TrainRetrieval(Retrieval):
	def __init__(self, slots):
		self.slots = slots
		self.DATABASE_DIR = os.path.join(DIR_PATH,"SMPdatabase/train/")

	def retrieval(self):
		file_tail = self.slots['start_date'][5:]
		f = self.compare_date(file_tail, terminalDay = 17)
		res = self.handle(f, self.slots['start_date'])
		return res

	def search(self, datas, slots, res):
		tickets = []
		start_city = slots['start_city'].encode('utf-8')
		arrival_city = slots['arrival_city'].encode('utf-8')
		for t_ticket in datas:
			if start_city in t_ticket['originStation'] and\
				arrival_city in t_ticket['terminalStation']:
				if 'originStation' in self.slots and \
					self.slots['originStation'].encode('utf-8') != t_ticket['originStation']:
					continue
				if 'terminalStation' in self.slots and \
					self.slots['terminalStation'].encode('utf-8') != t_ticket['terminalStation']:
					continue
				if slots.has_key('seats'):
					prices = []
					for item in t_ticket['price']:
						if item['name'].decode('utf-8') in slots['seats']:
							prices.append(item)
					if len(prices) == 0:
						continue
					else:
						t_ticket['price'] = prices
				if slots.has_key('price') and slots['price'].has_key('num'):
					prices = []
					for price in t_ticket['price']:
						if not deletePrice(self.slots, price['value']):
							prices.append(price)
					if len(prices) == 0:
						continue
					else:
						t_ticket['price'] = prices
				tickets.append(Train(t_ticket, start_city, arrival_city))
		return tickets

class HotelRetrieval(object):
	def __init__(self, slots):
		self.slots = slots
		self.DATABASE_DIR = os.path.join(DIR_PATH,"SMPdatabase/hotel/hotel/")

	'''
	0:数据库中无结果
	1:返回所查询的结果
	2:文件读取异常
	'''
	def retrieval(self):
		res = {}
		file_name = os.path.join(self.DATABASE_DIR,self.slots['city'].encode('utf-8'))
		try:
			datas = pkl.load(open(file_name,'r'))
		except Exception,e:
			print e
			res['status'] = 2
			return res
		hotels = self.search(datas, self.slots)
		if len(hotels) == 0:
			res['status'] = 0
			return res
		else:
			res['status'] = 1
			res['hotels'] = hotels
		return res

	
	'''
	搜索特定area的酒店，若无area限制，返回某个city所有的酒店
	酒店名限制的不在这个地方处理。
	'''
	def search(self, datas, slots):
		hotels = []
		for d in datas:
			if slots['city'].encode('utf-8') in d['city']:
				if slots.has_key('area'):
					if slots['area'].encode('utf-8') not in d['address']:
						continue
				if slots.has_key('price') and slots['price'].has_key('num'):
					if deletePrice(self.slots, d['price']) == 1:
						continue
				hotels.append(Hotel(d))
		return hotels




if __name__ == '__main__':
	#slot:utf-8
	slots = {'city':'哈尔滨','area':'南岗区'}
	retrieval = HotelRetrieval(slots)
	res = retrieval.retrieval()
	print res
	tickets = res['hotels']
	for t in tickets:
		print t

