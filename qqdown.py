#!/usr/bin/python

# QQDownload network interface

import qqweb
from common import *

XFJSON_URL="http://lixian.qq.com/handler/xfjson.php"

class QQDownException(Exception): pass

class QQDown(qqweb.QQWeb):
    @staticmethod
    def join_mid(mid):
        return reduce(lambda a,x:a+str(x)+"n",mid,"")[:-1] if isinstance(mid,list) else mid

    def qqdown_rpc(self,url,method="GET",**kwargs):
        '''
        Performs a qqdown formatted json rpc to url and return python-native result

        will remove callback function
        check result, raise exception if failed
        remove result and return data list

        Example:
        ['callback',{'result':0,'data':['errcode':'0','result':0,'id':'1234567']}]
        will be transcode to
        ['errcode':'0','result':0,'id':'1234567']
        '''
        ret=self.json_rpc(url,method,**kwargs)[1]
        if ret['result']!=0:
            raise QQDownException(ret['err_msg'])
        return ret['data']

    def __init__(self,username,password,is_pass_md53=False):
        qqweb.QQWeb.__init__(self,username,password,is_pass_md53)

    def add_task(self,fileurl,filename,filesize=0):
        data=dict(
                cmd='add_task',
                r  =random(),
                url=fileurl,
                fn =filename
                )
        return self.qqdown_rpc(XFJSON_URL,"POST",data=data)

    def add_bt_task(self,**kwargs):
        pass
    def add_torrent(self,filename):
        pass
    def add_torrent_from_url(self,url):
        pass

    def get_task_list(self):
        return self.qqdown_rpc(XFJSON_URL,query=dict(cmd='get_task_list',r=random()))

    def get_task_status(self,cur_ids):
        return self.get_task_list()
        '''
        return self.qqdown_rpc(XFJSON_URL,query=dict(
            cmd='get_task_status',
            r=random(),
            cids=QQDown.join_mid(cur_ids)
            ))
        '''

    def del_task(self,mid):
        data=dict(
                cmd ='del_task',
                r   =random(),
                tids=QQDown.join_mid(mid)
                )
        return self.qqdown_rpc(XFJSON_URL,"POST",data=data)

    def get_http_url(self,mid):
        pass

    def __repr__(self):
        return "<qqdown.QQDown object with user '%s'>"%self.username
