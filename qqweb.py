#!/usr/bin/python

# QQWeb interface

import json_rpc
from common import *

def prompt_for_verifycode(vc):
    from os import system
    fn='/tmp/vc.png'
    fd=open(fn,'wb')
    fd.write(vc)
    fd.close()
    system("display "+fn)
    return raw_input()

class QQWeb(json_rpc.Json_RPC):
    def __init__(self,username,password,is_pass_md53=False):
        self.username=username
        json_rpc.Json_RPC.__init__(self)
        if not is_pass_md53:
            password=md5_3(password)
        
        appid=567008010
        # Get Verify Code
        ret=self.json_rpc("http://ptlogin2.qq.com/check",
                          query=dict(uin=username,appid=appid,r=random())
                         )
        verifycode=ret[2]
        if ret[1]=='1':
            # TODO: Process Captcha Here
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
            raise LoginException(ret[5])

    def __repr__(self):
        return "<qqweb.QQWeb object with user '%s'>"%self.username
