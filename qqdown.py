#!/usr/bin/python

# QQDownload network interface

import qqweb
from bencode import bdecode
from common import *

XFJSON_URL="http://lixian.qq.com/handler/xfjson.php"

class QQDownException(Exception): pass

class QQDown(qqweb.QQWeb):
    def qqdown_rpc(self,url,method="GET",**kwargs):
        '''
        Performs a qqdown formatted json rpc to url and return python-native result
        Mainly for internal use

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

    def add_task(self,fileurl,filename="",filesize=0):
        ''' Add Task for URL '''

        # Guess filename
        if filename=="":
            filename=fileurl.split('?')[0].split('/')[-1] or "index.html"

        data=dict(
                cmd='add_task',
                r=random(),
                url=fileurl,
                fn=filename
                )
        return self.qqdown_rpc(XFJSON_URL,"POST",data=data)

    def add_bt_task(self,info_web):
        '''
        Actually submit bt task
        
        See also: read_torrent

        '''
        data=dict(
                cmd='add_bt_task',
                r=random(),
                hash=info_web['hash'],
                taskname=info_web['name'],
                index=join_component(info_web['files'],'#','file_index'),
                filesize=join_component(info_web['files'],'#','file_size_ori'),
                filename=join_component(info_web['files'],'#','file_name'),
                )

        return self.qqdown_rpc(XFJSON_URL,"POST",data=data)


    def read_torrent(self,torrent):
        '''
        Read info of a torrent from a bytestring

        return a dict like:
        {'files': [{'file_index': 0,
                    'file_name': 'tmp1/tmp2/b.txt',
                    'file_size': '0.01KB',
                    'file_size_ori': 7},
                   {'file_index': 1,
                    'file_name': 'tmp1/a.txt',
                    'file_size': '0KB',
                    'file_size_ori': 0},
                   {'file_index': 2,
                    'file_name': 'a.txt',
                    'file_size': '0KB',
                    'file_size_ori': 0}],
         'hash': 'asdfasdf',
         'name': 'tmp'}

        You can (optionally) remove some entries from `files' list
        and call add_bt_task by the dict to actually submit the bt task

        '''

        info_web=self.json_rpc(
                'http://lixian.qq.com/handler/bt_handler.php?cmd=readinfo',
                'POST',
                file=[('myfile','a.torrent',torrent)]
                )
        info_local=bdecode(torrent)['info']

        if info_web['ret']!=0:
            raise QQDownException(info_web['msg'])
        del info_web['ret']

        # Fix path based on local parse result
        l_local=info_local['files']
        l_web=info_web['files']
        for i in xrange(len(l_web)):
            if l_local[i]['length']!=l_web[i]['file_size_ori']:
                raise Exception("File size mismatch, Program Error?!")
            if l_local[i].has_key('path.utf-8'):
                l_web[i]['file_name']=join(l_local[i]['path.utf-8'],'\\')
            else:
                l_web[i]['file_name']=join(l_local[i]['path'],'\\')

        return info_web

    def add_torrent(self,torrent):
        ''' Helper method to add all files in a torrent from a bytestring '''
        self.add_bt_task(self.read_torrent(torrent))

    def get_task_list(self):
        ''' Get List of task status '''
        return self.qqdown_rpc(XFJSON_URL,query=dict(cmd='get_task_list',r=random()))

    def get_task_status(self,cur_ids):
        ''' Get List of task status, currently same to get_task_list '''
        return self.get_task_list()
        '''
        return self.qqdown_rpc(XFJSON_URL,query=dict(
            cmd='get_task_status',
            r=random(),
            cids=join(cur_ids,'n')
            ))
        '''

    def del_task(self,mid):
        ''' Delete a or a list of task by id '''
        data=dict(
                cmd ='del_task',
                r   =random(),
                tids=join(mid,'n')
                )
        return self.qqdown_rpc(XFJSON_URL,"POST",data=data)

    def get_http_url(self,mid):
        ''' Get HTTP Download URL by id '''
        raise NotImplemented()

    def __repr__(self):
        return "<qqdown.QQDown object with user '%s'>"%self.username

def get_torrent_from_file(filename):
    ''' Helper method to get torrent bytestring from a filename '''
    fd=file(filename,'rb')
    ret=fd.read()
    fd.close()
    return ret

def get_torrent_from_url(url):
    ''' Helper method to get torrent bytestring from url '''
    res=urllib2.urlopen(url)
    ret=res.read()
    res.close()
    return ret

def join(lst,separator):
    return separator.join(map(lambda x:str(x),lst))
def join_component(lst,separator,component):
    return separator.join(map(lambda x:str(x[component]),lst))

