#!/usr/bin/python

# Json RPC

import urllib2
from urllib import urlencode
from urllib2 import Request
from mimetypes import guess_type
from cookielib import MozillaCookieJar
from json import loads
from re import sub

class RPCError(Exception): pass

class Entity(object):
    def __init__(self,d={}):
        self.__dict__['___']=d.copy()

    def __getattr__(self,key):
        if self.__dict__['___'].has_key(key):
            return self.__dict__['___'][key]
        return None

    def __setattr__(self,key,value):
        self.__dict__['___'][key]=value

def recur_sub(pattern,repl,string):
    ''' Recursively sub string until nothing changed '''
    string2=""
    while string2!=string:
        string2=string
        string=sub(pattern,repl,string2)
    return string

def multipart_encode(data,files):
    ''' Encode a multipart/form-data packet '''
    BOUNDARY = '----------ThIs_Is_tHe_bouNdaRY_$'
    CRLF = '\r\n'
    L = []
    if data:
        for (key, value) in data.items():
            L.append('--' + BOUNDARY)
            L.append('Content-Disposition: form-data; name="%s"' % key)
            L.append('')
            L.append(value)
    if files:
        for (key, filename, value) in files:
            L.append('--' + BOUNDARY)
            L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
            L.append('Content-Type: %s' % guess_type(filename)[0] or 'application/octet-stream')
            L.append('')
            L.append(value)
    L.append('--' + BOUNDARY + '--')
    L.append('')
    body = CRLF.join(L)
    content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
    return content_type, body

class Json_RPC(object):
    def __init__(self):
        #self.cookie_jar=CookieJar()
        self.cookie_jar=MozillaCookieJar()
        self.opener=urllib2.build_opener(
                urllib2.HTTPCookieProcessor(self.cookie_jar),
                #urllib2.HTTPHandler(debuglevel=1),
                #urllib2.HTTPSHandler(debuglevel=1),
                )

    def load_cookie(self,filename):
        ''' Load Cookie from file '''
        self.cookie_jar.load(filename,ignore_discard=True)

    def save_cookie(self,filename):
        ''' Save Cookie to file '''
        self.cookie_jar.save(filename,ignore_discard=True)

    def json_rpc(self,url,method="GET",**kwargs):
        '''
        Performs a json rpc to url and return python-native result

        will remove try-catch statements, and
        reorganize function calls to list

        Example:
        try{callback({"result":0,"data":[]});}catch(e){}
        will be transcode to
        ['callback',{'result':0,'data':[]}]

        See also: http_rpc

        '''
        ret=self.http_rpc(url,method,**kwargs)
        ret=recur_sub(r'try{(.*)}catch\(.*\){.*};?',r'\1',ret)
        ret=recur_sub(r'(\w+)\((.*)\);?',r"['\1',\2]",ret)
        ret=recur_sub(r"'",r'"',ret)
        ret=loads(ret)
        return ret

    def http_rpc(self,url,method="GET",**kwargs):
        '''
        Perfoms a http rpc to url and return raw result

        url          base url to rpc
        method       'GET' or 'POST'
        query        query string passing by a dict
        data         post data passing by a dict
        file         post files passing by a list of 3-tuple: key, filename, data
                     ( this indicates multipart/form-data )
        
        '''
        kwe=Entity(kwargs)

        if method not in ['GET','POST']:
            raise RPCError("Method not in GET or POST")

        if kwe.query:
            url+="?"+urlencode(kwe.query)

        if method=='GET':
            request=Request(url)
        else:
            if not (kwe.data or kwe.file):
                raise RPCError("POST with no data")

            if kwe.file:
                content_type,data=multipart_encode(kwe.data,kwe.file)
                request=Request(url,data)
                request.add_header('Content-Type', content_type)
            else:
                data=urlencode(kwe.data)
                request=Request(url,data)

        request.add_header('User-Agent',
            "Mozilla/5.0 (Ubuntu; X11; Linux x86_64; rv:8.0) Gecko/20100101 Firefox/8.0"
            )
        request.add_header('Accept-Charset',"UTF-8")
        '''
        request.add_header('Referer',
            "http://ui.ptlogin2.qq.com/cgi-bin/login?uin=&appid=567008010&f_url=loginerroralert&hide_title_bar=1&style=1&s_url=http%3A//lixian.qq.com/main.html&lang=0&enable_qlogin=1&css=http%3A//imgcache.qq.com/ptcss/r1/txyjy/567008010/login_mode_new.css%3F"
            )
        '''

        response=self.opener.open(request)
        ret=response.read()
        response.close()

        #print "\033[33m"+str(self.cookie_jar)+"\033[0m"

        # FIXME: An Ugly hack to Tencent server's charset indicator using BOM header
        if ret.startswith('\xef\xbb\xbf'):
            ret=ret[3:]

        return ret
