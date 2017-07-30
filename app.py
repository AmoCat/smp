#coding:utf-8

from flask import Flask, render_template, jsonify, request
from language_understanding import TrainCommander, FlightCommander, HotelCommander
from language_understanding.common import *
import json
import traceback
import re
from intent_indentity import *
from copy import deepcopy
import os

app = Flask('benben-lu')
app.config.from_object('config')

from flask.ext.bootstrap import Bootstrap
Bootstrap(app)

STATUS_SUCCESS = 0
STATUS_WAITING = 1
STATUS_INTERUPT = 2
STATUS_CONFITM = 3

MAX_ALIVE_TIME = 10

MSG_TYPE_TEXT = 'text'
MSG_TYPE_TICKET = 'tickets'

CONTEXT_PATH = os.path.join(os.path.dirname('__file__'),'context/')
RESP_KEY = {"flight":['price','cabin','rate', 'airline'],"train":['train_type','seats','price'],"hotel":['price']}

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/module/instruction_execution', methods=['POST'])
def get_hotel_reply():
    app.logger.info(request.json)
    sent = request.json.get('query')
    #context = request.json.get('context')
    session_id = request.json.get('session_id')
    timestamp = request.json.get('timestamp')
    token = request.json.get('token')
    metafield = {}
    intents = get_intent(sent)

    
    try:
        context = eval(open(CONTEXT_PATH + session_id,'r').read().strip())
    except Exception,e:
        context = request.json.get('context')

    print "context",context

    if not context.has_key('pre_info'):
        context['pre_info'] = {}
 
    if len(intents) == 0 and (not context.has_key('intents') or len(context['intents']) == 0):
        print "######len(intents) == 0 and (not context.has_key('intents') or len(context['intents']) == 0)"
        if context.has_key('last_finish_intent'):
            p = detect_price_change(sent)
            if p == None:
                print "###detect_price_change(sent) == None"
            if context['last_finish_intent'] == 'flight' and (p or detect_f_change):
                context['intents'] = ['flight']
            elif context['last_finish_intent'] == 'train' and (p or detect_t_change):
                print "###change_t"
                context['intents'] = ['train']
            elif context['last_finish_intent'] == 'hotel' and p:
                context['intents'] = ['hotel']
        else:
            f = open(CONTEXT_PATH + session_id, 'w')
            f.write(str(context))
            f.close()
            return jsonify({'msg_type': MSG_TYPE_TICKET,'status': STATUS_SUCCESS, 'reply': '无查询意图', 'context': context, 'metafield':{}})
    elif len(intents) != 0:
        if not context.has_key('intents') or context['intents'] == None:
            context['intents'] = intents
        else:      
            for intent in intents:
                if intent not in context['intents']:
                    context['intents'].append(intent)
    for intent in context['intents']:
        if intent == 'flight':
            commander = FlightCommander()
            res = reply(commander, sent, context, metafield, session_id, 'flight')
        elif intent == 'train':
            commander = TrainCommander()
            res = reply(commander, sent, context, metafield, session_id, 'train')
        elif intent == 'hotel':
            commander = HotelCommander()
            res = reply(commander, sent, context, metafield, session_id, 'hotel')
        return res

def reply(commander, sent, context, metafield, session_id, intent_str):

    old_intent = deepcopy(context['intents'])
    pre_info = deepcopy(context['pre_info']) if context.has_key('pre_info') else {}
    app.logger.info('INPUT: ' + '\t'.join([sent, str(context)]))
    try:
        if metafield and 'ltp' in metafield.keys():
            ltp = metafield.get('ltp')
            seg = ltp.get('seg').split()
            pos = ltp.get('pos').split()
            nes = ltp.get('ner').split()
            status, reply, context = commander.get_reply_with_lexical(sent, seg, pos, nes, context)
        else:
            status, reply, context = commander.get_reply(sent, context)
    except Exception as e:
        traceback.print_exc()
        app.logger.info(str(e))
        status = STATUS_INTERUPT
        reply = ''
        context = context
    app.logger.info('OUTPUT: ' + '\t'.join([str(status), reply, str(context)]))
    msg_type = MSG_TYPE_TEXT
    if status == STATUS_SUCCESS:
            not_find = re.search("没有找到",reply)
            before_date = re.search("昨天",reply)
            unsupported_city = re.search("不支持的",reply)
            error = re.search("有误",reply)
            if not (not_find or before_date or unsupported_city or error):
                msg_type = MSG_TYPE_TICKET
    if status == STATUS_SUCCESS and intent_str in old_intent:
        old_intent.remove(intent_str)
        print type(context),type(old_intent)
        context['intents'] = old_intent
        context['last_finish_intent'] = intent_str
        context['last_finish_slot'] = context['slots']
        for k in RESP_KEY[intent_str]:
            if context['pre_info'].has_key(k):
                context['pre_info'].pop(k)
    
    f = open(CONTEXT_PATH + session_id, 'w')
    f.write(str(context))
    return jsonify({'msg_type': msg_type,'status': status, 'reply': reply, 'context': context, 'metafield':{}})