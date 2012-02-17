#!/usr/bin/python
#QQDown -- An open-sourced implementation of tencent offline download
#Copyright (C) 2011-2012 Tydus <Tydus@Tydus.org>
#
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Json RPC

import urllib2
from urllib import urlencode
from urllib2 import Request
from mimetypes import guess_type
from cookielib import MozillaCookieJar
from json import loads
from re import search,sub

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

        will extract dict or list from result

        Example:
        try{callback({'result':0,'data':[]});}catch(e){}
        will be transcode to
        {"result":0,"data":[]}

        See also: http_rpc

        '''
        ret=self.http_rpc(url,method,**kwargs)
        ret=sub(r'try{(.*)}catch\(.*\){.*};?',r'\1',ret)
        ret=(search(r'{.+}',ret) or search(r'\[.+\]',ret)).group()
        #ret=sub(r"'",r'"',ret)
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
        elif kwe.file:
            content_type,data=multipart_encode(kwe.data,kwe.file)
            request=Request(url,data)
            request.add_header('Content-Type', content_type)
        elif kwe.data:
            data=urlencode(kwe.data)
            request=Request(url,data)
        else:
            raise RPCError("POST with no data")

        request.add_header('User-Agent',
            "Mozilla/5.0 (Ubuntu; X11; Linux x86_64; rv:8.0) Gecko/20100101 Firefox/8.0"
            )
        request.add_header('Accept-Charset',"UTF-8")

        response=self.opener.open(request)
        ret=response.read()
        response.close()

        #print "\033[33m"+str(self.cookie_jar)+"\033[0m"

        # FIXME: An Ugly hack to Tencent server's charset indicator using BOM header
        if ret.startswith('\xef\xbb\xbf'):
            ret=ret[3:]

        return ret
