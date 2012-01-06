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

# QQWeb interface

import json_rpc
from random import random
from hashlib import md5
from string import upper

class QQLoginException(Exception): pass

def md5_3(a):
    ''' Performs an 3-time MD5 (md5_3 as Tencent spec) '''
    a=md5(a).digest()
    a=md5(a).digest()
    return upper(md5(a).hexdigest())

def prompt_for_verifycode(vc):
    from os import system
    fn='/tmp/vc.png'
    fd=open(fn,'wb')
    fd.write(vc)
    fd.close()
    system("display "+fn)
    return raw_input('Input verifycode: ')

class QQWeb(json_rpc.Json_RPC):
    def __init__(self,username,password,is_pass_md53=False,nologin=False):
        self.username=username
        json_rpc.Json_RPC.__init__(self)
        if not is_pass_md53:
            password=md5_3(password)

        if nologin:
            return
        
        appid=567008010
        # Get Verify Code
        ret=self.json_rpc("http://ptlogin2.qq.com/check",
                          query=dict(uin=username,appid=appid,r=random())
                         )
        verifycode=ret[2]
        if ret[1]=='1':
            ret=self.http_rpc("http://captcha.qq.com/getimage",
                              query=dict(uin=username,
                                      aid=appid,
                                      r=random(),
                                      vc_type=verifycode)
                             )
            verifycode=prompt_for_verifycode(ret)

        password_md5=md5(password+verifycode.upper()).hexdigest()
        ret=self.json_rpc("http://ptlogin2.qq.com/login",
                          query=dict(u=username,
                                     p=password_md5,
                                     verifycode=verifycode,
                                     aid=appid,
                                     u1="http://lixian.qq.com/main.html",
                                     h=1,
#                                     ptredirect=1,
#                                     ptlang=2052,
                                     from_ui=1,
#                                     dumy="",
#                                     mibao_css="",
                                     fp="loginerroralert"
#                                     action="2-13-237255",
                                    )
                         )
        if ret[1]!='0':
            # Login Failed
            raise QQLoginException((ret[1],ret[5]))

    def __repr__(self):
        return "<qqweb.QQWeb object with user '%s'>"%self.username
