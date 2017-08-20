#!/usr/bin/env python
# test harness for policy python code
_message = {}
class Message:
    def __init__(self):
        pass
    def getInboundProperty(self,key):
        return _message[key] if key in _message else ''
    def setInboundProperty(self,key,value):
        _message[key] = value

message = Message()
message.setInboundProperty('http.listener.path','/v1/api/*')
message.setInboundProperty('http.method','GET')
message.setInboundProperty('http.request.path','/v1/api/things')
payload = ''
flowVars={
    '_agwTokenContext':'{"access_token":{"uid":"ac45@columbia.edu","username":"ac45@columbia.edu","group":"read openid create demo-netphone-admin update auth-columbia delete"},"scope":"auth-columbia read openid","token_type":"urn:pingidentity.com:oauth2:validated_token","expires_in":7195,"client_id":"64575d23b8504c9bb1e9e7ff558c3cd3"}'
}

###
# paste below the generated python code from for example ~/AnypointStudio/workspace/.mule/policies/24940-235285.xml
# SNIP - SNIP - SNIP
###
