#!/usr/bin/env python
# coding=utf-8

import cPickle as pkl

def get_station():
    prefix = "2017-04-"
    out = open("station_name.txt",'w')
    stations = []
    tail = [u"南",u"北",u"东",u"西"]
    print type(tail[0])
    for i in range(18,31):
        f = open(prefix + str(i)).read().strip().split('\n')
        datas = []
        for line in f:
            datas.extend(eval(line.strip()))
        d = {}
        for data in datas:
            print type(data['originStation'][-1]),data['originStation'].decode('utf-8')[-1]
            if data['originStation'].decode('utf-8')[-1] not in tail:
                tmp = data['originStation'] + '站'
                if not d.has_key(tmp):
                    d[tmp] = 1
                    stations.append(tmp.decode('utf-8'))
                    out.write(tmp+'\n')
            elif not d.has_key(data['originStation']):
                d[data['originStation']] = 1
                stations.append(data['originStation'].decode('utf-8'))
                out.write(data['originStation']+'\n') 
            print type(data['terminalStation'][-1]),data['terminalStation'].decode('utf-8')[-1]
            if data['terminalStation'].decode('utf-8')[-1] not in tail:
                tmp = data['terminalStation'] + '站'
                if not d.has_key(tmp):
                    d[tmp] = 1
                    stations.append(tmp.decode('utf-8'))
                    out.write(tmp+'\n')
            elif not d.has_key(data['terminalStation']):
                d[data['terminalStation']] = 1
                stations.append(data['terminalStation'].decode('utf-8'))
                out.write(data['terminalStation']+'\n')
    pkl.dump(stations,open('station_name.pkl', 'w'))


if __name__ == "__main__":
    get_station()
