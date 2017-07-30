# coding: utf-8
import requests
import json

url = "http://127.0.0.1:9527/module/instruction_execution"
#url = "http://0.0.0.0:9527/module/instruction_execution/train"



query = '后天从北京到哈尔滨的火车票'
context = {'test':'test'}
token = "123"
timestap = "123"
session_id = "1"
values = {'query': query, 'context':context, 'session_id':session_id,'metafield': ""}

response = requests.post(url, json = values)
print response.json()
