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

# QQDownload network interface

import qqweb
from urllib2 import urlopen
from bencode import bdecode
from random import random

XFJSON_URL="http://lixian.qq.com/handler/xfjson.php"

class QQDownException(Exception): pass

error_desc={
        '-10001':"HTTP Communication failed",
        '-10005':"Empty Response",
        '-10007':"XML Parsing Error",
        '-10008':"Returning Data Malformed",
        
        '-11001':"Wrong Parameter",
        '-11002':"Not Logged in",
        '-11003':"Not VIP",
        '-11004':"Checking for VIP failed",
        '-11005':"Checking for VIP Level failed",
        '-11006':"Get Task List failed",
        '-11007':"Get Task Status failed",
        '-11008':"Add Task failed",
        '-11009':"Del Task failed",
        '-11010':"",
        '-11011':"Not Priviliged User",
        }

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
        if ret.has_key('result') and ret['result']!=0:
            raise QQDownException({'desc':error_desc[ret['result']],'raw':ret})
        if ret.has_key('status') and ret['status']!=0:
            raise QQDownException({'desc':ret['status'],'raw':ret})
        return ret['data']

    def add_task(self,fileurl,filename="",filesize=0):
        '''
        Add Task according to a URL
        
        Return a list like:
        [{u'SHA': u'2446c16c6176e9f9f717eefdfc62559f297be940',
          u'file_name': u'dfsa',
          u'file_url': u'aHR0cDovL3d3dy5iYWlkdS5jb20vZGZzYQ==',
          u'id': u'1629381383632120927'}]
        
        '''

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

        Return a list like:
        [{u'bt_id': u'd6c8299a4db8e922b02da9b4acbfc4739e6ab8df_0',
          u'file_name': u'tmp1\\\\tmp2\\\\b.txt',
          u'file_size': u'7',
          u'id': u'1629381383632121173'},
         {u'bt_id': u'd6c8299a4db8e922b02da9b4acbfc4739e6ab8df_1',
          u'file_name': u'tmp1\\\\a.txt',
          u'file_size': u'0',
          u'id': u'1629381383634713173'}]
        
        See also: read_torrent

        '''
        data=dict(
                cmd='add_bt_task',
                r=random(),
                hash=info_web['hash'],
                taskname=info_web['name'].encode('utf-8'),
                index=join_component(info_web['files'],'#','file_index'),
                filesize=join_component(info_web['files'],'#','file_size_ori'),
                filename=join_component(info_web['files'],'#','file_name').encode('utf-8'),
                )
        return self.qqdown_rpc(XFJSON_URL,"POST",data=data)


    def read_torrent(self,torrent):
        '''
        Read info of a torrent from a bytestring

        return a dict like:
        {'files': [{'file_index': 0,
                    'file_name': 'tmp1\\\\tmp2\\\\b.txt',
                    'file_size': '0.01KB',
                    'file_size_ori': 7},
                   {'file_index': 1,
                    'file_name': 'tmp1\\\\a.txt',
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

        info_local=bdecode(torrent)['info']
        info_web=self.json_rpc(
                'http://lixian.qq.com/handler/bt_handler.php?cmd=readinfo',
                'POST',
                file=[('myfile','a.torrent',torrent)]
                )

        if info_web['ret']!=0:
            raise QQDownException(info_web['msg'])
        del info_web['ret']


        if info_local.has_key('files'):
            # This torrent is a multi-file one
            l_local=info_local['files']
            l_web=info_web['files']

            # Fix path based on local parse result
            for i in l_web:
                ind=i['file_index']
                if l_local[ind].has_key('path.utf-8'):
                    i['file_name']='\\'.join(l_local[ind]['path.utf-8']).decode('utf-8')
                elif info_local.has_key('encoding'):
                    i['file_name']='\\'.join(l_local[ind]['path']).decode(info_local['encoding'])
                else:
                    i['file_name']='\\'.join(l_local[ind]['path']).decode('utf-8')
        else:
            # This torrent only contains a single file
            # We don't need to fix it because it doesn't contains a dir
            pass

        return info_web

    def add_torrent(self,torrent):
        ''' Helper method to add all files in a torrent from a bytestring '''
        return self.add_bt_task(self.read_torrent(torrent))

    def get_task_list(self):
        '''
        Get List of task status
        
        Return a list like:
        [{u'acc_cookie': None,
          u'acc_url': '',
          u'addtime': u'1325851661',
          u'comp_size': u'6759',
          u'dl_status': u'12',
          u'file_name': u'index.html',
          u'file_size': u'6759',
          u'file_url': u'aHR0cDovL3d3dy5iYWlkdS5jb20vaW5kZXguaHRtbA==',
          u'hash': u'B91378AFE2E92401E2839E8A7FC65ABA1F055448',
          u'id': u'1629381383632118795',
          u'left_time': u'1040184'},
         {u'acc_cookie': None,
          u'acc_url': '',
          u'addtime': u'1325851831',
          u'bt_id': u'D6C8299A4DB8E922B02DA9B4ACBFC4739E6AB8DF_0',
          u'comp_size': u'0',
          u'dl_status': u'6',
          u'file_name': u'tmp1\\\\tmp2\\\\b.txt',
          u'file_size': u'7',
          u'file_url': u'aHR0cDovLzE5Mi4xNjguMS4yMzMvPyYmdHhmX2ZpZD0=',
          u'hash': '',
          u'id': u'1629381383632118967',
          u'left_time': u'1040400',
          u'link_type': u'BT'}]

        Go ahead and filter out the data you needed
        
        '''

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
        '''
        Delete a or a list of task by id
        
        Return a list like:
        [{u'errcode': u'0', u'id': u'1629381383632120927', u'result': u'0'},
         {u'errcode': u'0', u'id': u'1629381383632118967', u'result': u'0'}]
            
        '''
        data=dict(
                cmd ='del_task',
                r   =random(),
                tids=join(mid,'n')
                )
        return self.qqdown_rpc(XFJSON_URL,"POST",data=data)

    def get_http_url(self,hash):
        '''
        Get HTTP Download URL by hash

        Return a dict like:
        {u'cookie': u'75000578',
         u'url': u'http://xfwb.store.qq.com:443/?.....'}

        '''
        data=dict(
                hash=hash,
                callback="callback"
                )
        return self.qqdown_rpc('http://lixian.qq.com/handler/get_http_url.php',
                query=data
                )

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
    res=urlopen(url)
    ret=res.read()
    res.close()
    return ret

def join(lst,separator):
    return separator.join(map(lambda x:unicode(x),lst))
def join_component(lst,separator,component):
    return separator.join(map(lambda x:unicode(x[component]),lst))

