#!/usr/bin/python

# Json RPC

from common import *
from urllib2 import Request

class Json_RPC(object):
    def __init__(self):
        self.cookie_jar=CookieJar()
        self.opener=urllib2.build_opener(
                urllib2.HTTPCookieProcessor(self.cookie_jar),
                #urllib2.HTTPHandler(debuglevel=1),
                #urllib2.HTTPSHandler(debuglevel=1),
                )

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
        ret=recur_sub(r'(\w+)\((.*)\);',r"['\1',\2]",ret)
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
        multipart    if we need multipart data, default urlencoded
        
        '''
        kwe=Entity(kwargs)

        if method not in ['GET','POST']:
            raise RPCError("Method not in GET or POST")

        if kwe.query:
            url+="?"+urlencode(kwe.query)



        if method=='GET':
            request=Request(url)
        else:
            if not kwe.data:
                raise RPCError("POST with no data")

            if kwe.multipart:
                # TODO: Handle multipart here
                raise NotImplemented()
                data=None
            else:
                data=urlencode(kwe.data)
            request=Request(url,data)

        request.add_header('User-Agent',
            "Mozilla/5.0 (Ubuntu; X11; Linux x86_64; rv:8.0) Gecko/20100101 Firefox/8.0"
            )
        request.add_header('Referer',
            "http://ui.ptlogin2.qq.com/cgi-bin/login?uin=&appid=567008010&f_url=loginerroralert&hide_title_bar=1&style=1&s_url=http%3A//lixian.qq.com/main.html&lang=0&enable_qlogin=1&css=http%3A//imgcache.qq.com/ptcss/r1/txyjy/567008010/login_mode_new.css%3F"
            )

        response=self.opener.open(request)

        #print "\033[33m"+str(self.cookie_jar)+"\033[0m"

        ret=response.read()
        response.close()
        return ret
