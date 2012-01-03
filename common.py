#!/usr/bin/python

# Common Library for qqdown

from hashlib import md5
from string import upper
from random import random
from json import loads
from re import sub
from urllib import urlencode
from cookielib import CookieJar
import urllib2

class LoginException(Exception): pass
class RPCError(Exception): pass


def md5_3(a):
    ''' Performs an 3-time MD5 (md5_3 as Tencent spec) '''
    a=md5(a).digest()
    a=md5(a).digest()
    return upper(md5(a).hexdigest())

def prompt(*args):
    ''' Prompt something or do nothing '''
    for i in args:
        print i,
    print

def recur_sub(pattern,repl,string):
    ''' Recursively sub string until nothing changed '''
    string2=""
    while string2!=string:
        string2=string
        string=sub(pattern,repl,string2)
    return string

class Entity(object):
    def __init__(self,d={}):
        self.__dict__['___']=d.copy()

    def __getattr__(self,key):
        if self.__dict__['___'].has_key(key):
            return self.__dict__['___'][key]
        return None

    def __setattr__(self,key,value):
        self.__dict__['___'][key]=value

