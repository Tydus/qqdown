#!/bin/bash

if [ $# -lt 2 ]; then
    echo "Login"
    echo "$0 USERNAME PASSWORD"
    echo "$0 USERNAME md53 PASSWORD_MD53"
    exit
fi

USERNAME=$1
shift
PASSWORD=$1
shift
if [ 'md53' = ${PASSWORD} -a "$1" ]; then
    PASSWORD_MD53=$1
else
    PASSWORD_MD53=`./md5_3 ${PASSWORD}`
fi

function prompt {
    echo "$@"
}

APPID="567008010"

prompt "Get verify code"
CHECKURL="http://ptlogin2.qq.com/check?uin=${USERNAME}&appid=${APPID}&r=0.${RANDOM}"
VERIFYCODE=`curl -c cookie ${CHECKURL} -s| awk -F"'" '{printf "%s",$4}'`

PASSWORDHASH=`python << EOF
import hashlib
import string
print string.upper(hashlib.md5('${PASSWORD_MD53}${VERIFYCODE}').hexdigest())
EOF`

prompt "Login"
LOGINURL="http://ptlogin2.qq.com/login?u=${USERNAME}&p=${PASSWORDHASH}&verifycode=${VERIFYCODE}&aid=${APPID}&u1=http%3A%2F%2Flixian.qq.com%2Fmain.html&h=1&ptredirect=1&ptlang=2052&from_ui=1&dumy=&fp=loginerroralert&action=2-13-273255&mibao_css="
LOGINRES=`curl -b cookie ${LOGINURL} -c cookie -s`

if [ '0' != `echo ${LOGINRES} | cut -d"'" -f2` ]; then
    echo ${LOGINRES}
    rm -f cookie
    exit
fi
