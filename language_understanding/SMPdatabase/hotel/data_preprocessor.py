#!/usr/bin/env python
# coding=utf-8

import os
import cPickle as pkl
from copy import deepcopy


DIR_PATH = os.path.join(os.path.dirname(__file__),'hotel')

def preprocessor():
	datas = open("hotel.txt",'r').read().strip().split('\n')
	city_name_file = open('cities_name.txt','w')
	dicts = {}
	for line in datas:
		hotel = eval(line)
		tmp = hotel['city']
		cities = deepcopy(tmp)
		cities = cities.strip().replace('）',"").replace('（','/').split('/')
		for city in cities:
			city = city.strip()
			if city == '':
				continue
			if(dicts.has_key(city)):
				dicts[city].append(hotel)
			else:
				dicts[city] = []
				dicts[city].append(hotel)
	for k,v in dicts.items():
		file_name = os.path.join(DIR_PATH,k)
		print file_name
		city_name_file.write(k+'\n')
		pkl.dump(v,open(file_name,'w'))

if __name__ == '__main__':
	preprocessor()