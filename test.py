#!/usr/bin/env python
# standalone test harness for policy python code
from optparse import OptionParser

_message = {}
class Message:
    def __init__(self):
        pass
    def getInboundProperty(self,key):
        return _message[key] if key in _message else ''
    def setInboundProperty(self,key,value):
        _message[key] = value

parser = OptionParser()
parser.add_option('-g','--group',
                  type='string',
                  default='read openid create demo-netphone-admin update auth-columbia delete',
                  help='group list from idp adapter [default: %default]')
parser.add_option('-s','--scope',
                  type='string',
                  default='auth-columbia read openid',
                  help='scope list from access token [default: %default]')
parser.add_option('-r','--request',
                  type='string',
                  default='/v1/api/things',
                  help='HTTP request path: [default: %default]')
parser.add_option('-l','--listener',
                  type='string',
                  default='/v1/api/*',
                  help='HTTP listener path. [default: %default]')
parser.add_option('-m','--method',
                  type='string',
                  default='GET',
                  help='HTTP method [default: %default]')
parser.parse_args()

message = Message()
message.setInboundProperty('http.listener.path',parser.values.listener)
message.setInboundProperty('http.method',parser.values.method.upper())
message.setInboundProperty('http.request.path',parser.values.request)

payload = ''
# flowVars is a map but the value of _agwTokenContext is a string (that contains JSON)
flowVars={'_agwTokenContext':'{"access_token":{"uid":"ac45@columbia.edu","username":"ac45@columbia.edu","group": "%s"},"scope": "%s","token_type":"urn:pingidentity.com:oauth2:validated_token","expires_in":7195,"client_id":"64575d23b8504c9bb1e9e7ff558c3cd3"}'%(parser.values.group,parser.values.scope)}

import logging
log = logging.getLogger()
if not log.handlers:
  handler = logging.StreamHandler()
  formatter = logging.Formatter('%(levelname)-5s %(asctime)s %(message)s')
  handler.setFormatter(formatter)
  log.addHandler(handler)
log.setLevel(logging.DEBUG)

###
# paste below the generated python code from for example ~/AnypointStudio/workspace/.mule/policies/24940-235285.xml
# SNIP - SNIP - SNIP
# and comment out the "from org.apache.log4j import *"!
###
