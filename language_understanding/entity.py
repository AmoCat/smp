#!/usr/bin/env python
#coding=utf-8


class Price(object):
    def __init__(self,price_dict):
        self.name = price_dict['name'] if price_dict.has_key('name') else ""
        self.value = price_dict['value']

    def __str__(self):
        rt = "%s\t¥%s\n"%(self.name,self.value)
        return rt

class Train(object):
    def __init__(self, item, startCity, arrivalCity):
        self.terminalStation = item['terminalStation']
        self.originStation = item['originStation']
        self.startCity = startCity
        self.arrivalCity = arrivalCity
        self.trainNo = item['trainNo']
        self.trainType = item['trainType']
        start = item['startTime'].split()
        arrival = item['arrivalTime'].split()
        self.startDate = start[0]
        self.startTime = start[1]
        self.arrivalDate = arrival[0]
        self.arrivalTime = arrival[1]
        self.runTime = item['runTime']
        self.prices = []
        for dict in item['price']:
            self.prices.append(Price(dict))

    def __str__(self):
        rt = "%s->%s\t%s\n"%(self.originStation,self.terminalStation,self.trainNo)
        rt += "%s\t%s->%s\t%s\n"%(self.startDate,self.startTime,self.arrivalDate,self.arrivalTime)
        for p in self.prices:
            rt += str(p)
        return rt

class FlightTicket(object):
    def __init__(self,dict):
        self.departCity = dict['departCity']
        self.arrivalCity = dict['arriveCity']
        self.flightNo = dict['flight']
        self.dPort = dict['dPort']
        self.aPort = dict['aPort']
        self.price = dict['price']
        self.rate = dict['rate']
        self.quantity = dict['quantity']
        self.standardPrice = dict['standardPrice']
        self.cabinInfo = dict['cabinInfo'].strip()
        start = dict['takeOffTime'].split()
        arrival = dict['arriveTime'].split()
        self.startDate = start[0]
        self.startTime = start[1]
        self.arrivalDate = arrival[0]
        self.arrivalTime = arrival[1]
        self.airline = dict['airline']

    def __str__(self):
        rt = "%s\t%s-%s\t%s\n"%(self.startDate,self.startTime,self.arrivalDate,self.arrivalTime)
        rt += "%s->%s\t%s\t¥%s\t折扣:%s\t%s\n"%\
                (self.dPort,self.aPort,self.cabinInfo,\
                 self.price,self.rate,self.airline)
        return rt


class Hotel(object):
    def __init__(self,dict):
        self.city = dict['city']
        self.name = dict['name']
        self.gpsLat = dict['gpsLat']
        self.price = dict['price']
        self.gpsLng = dict['gpsLng']
        self.address = dict['address']


    def __str__(self):
        rt ="%s\t¥%s"%(self.name,self.price)
        rt += "价格不详" if self.price == '0' else ""
        rt += "\n地址:\t%s\n"%(self.address)
        return rt

        
