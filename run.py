#coding:utf8
from app import app
import os

CONTEXT_PATH = os.path.join(os.path.dirname('__file__'),'context/1')

if __name__ == '__main__':
    #app.run(host='0.0.0.0', port = 9527, use_reloader=False)
    f = open(CONTEXT_PATH, 'w')
    f.write('{}')
    f.close()
    app.run(host='127.0.0.1', port = 3333)
    #app.run(host='0.0.0.0', port = 9527)
