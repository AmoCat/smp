#!/usr/bin/env python
# coding=utf-8

def get_airline():
    file = open('04-18','r').read().strip().split('\n')
    datas = []
    for line in file:
        datas.extend(eval(line.strip()))
    f = open('airline_name.txt','w')
    di = {}
    for data in datas:
        if di.has_key(data['airline']):
            continue
        f.write(data['airline'] + '\n')
        di[data['airline']] = 1
    f.close()

if __name__ == "__main__":
    get_airline()
