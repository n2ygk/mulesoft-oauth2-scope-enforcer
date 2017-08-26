import json
import re
import yaml
from pprint import pprint

httpVerbs = ['get','post','put','update','patch','delete']

oauth2Scopes = {} # default scopes for the given scheme name if not overidden in a securedBy
def securitySchemes(schemes):
  for s in schemes:
    if 'type' in schemes[s] and schemes[s]['type'].lower() == 'oauth 2.0':
      oauth2Scopes[s] = schemes[s]['scopes'] if 'scopes' in schemes[s] else []
  return

def securedBy(schemes): # the scheme name can be a string or a map key
  sl = []
  for s in schemes:
    if isinstance(s,str): # if the node is terminal then no overriding scopes
      if s in oauth2Scopes:
        sl = sl + oauth2Scopes[s] # use the defaults for this scheme name
    else: # there _might_ be an override
      for k in s: # should be a dict with one key.
        if 'scopes' in s[k]:
          sl = sl + s[k]['scopes']
        else:
          if k in oauth2Scopes:
            sl = sl + oauth2Scopes[s] 
    return sl

# make this look like the same keyvalue mustacheMap
def jsonParseResource(j,resource,mustacheMap):
  #print(">>>>>>>>>>>>>>ENTER")
  #pprint(j)
  for m in j:
    if isinstance(m,str): # ignore lists?
      if m[0] == '/':
        #print("<<<<<<<<<<<<<<<<<RECURSE %s"%resource+m)
        #pprint(j[m])
        mustacheMap = jsonParseResource(j[m],resource+m,mustacheMap)
      elif m.lower() in httpVerbs:
        method = m
        for mj in j[m]:
          if isinstance(mj,str) and mj.lower() == 'securedby':
            mr = method + ':' + re.sub('{.+}','.+',resource)
            #print("adding",{mr: j[m][mj]})
            mustacheMap.update({mr.replace('/','&#x2F;'): ' '.join(securedBy(j[m][mj]))})
      elif m.lower() == 'securityschemes':
        securitySchemes(j[m])
      else: 
        pass

  return mustacheMap

def ramlParse(s):
  mustacheMap = {}
  y = yaml.load(s.replace('!','')) # temporarily just ignore the !includes and so on
  #pprint(y)
  return jsonParseResource(y,'',mustacheMap)


ramlString = """
#%RAML 1.0  
title: demo-echo
version: v1
description: a demo app that uses Oauth2.0 Authorization Code grants
documentation: 
  - title: Introduction
    content: Write some markdown text _here_
  - title: What does this app do?
    content: |
      Not a hell of a lot. It returns the list of oauth scopes and groups.
#baseUri: https://columbia-demo-echo.cloudhub.io/{version}
baseUri: https://mocksvc.mulesoft.com/mocks/85d52e43-4825-42f8-a2a6-fcd2ad9d2aaa/{version}
securitySchemes: 
  oauth_2_0:
    type: OAuth 2.0
    description: |
      This API supports OAuth 2.0 for authorizing requests using PingFederate.
      Please note that MuleSoft will not actually implement any OAuth 2.0 scope enforcement
      as declared with a resource & method's `securedBy` unless you apply an one or more
      relevant API Manager Policies:
        - One of the `OAuth 2.0 protected` PingFederate policies.
        - The `OAuth 2.0 scope enforcement` custom policy.
    describedBy:
      headers:
        Authorization?:
          description: OAuth 2 access token. Use EITHER this or the access_token, not both.
          type: string
      queryParameters:
        access_token?:
          description: OAuth 2 access token. Use EITHER this or the Authorization header, not both.
          type: string
      responses:
        401:
          description: Bad or expired token.
        403:
          description: Bad OAuth request
    settings:
      authorizationUri: https://oauth.cc.columbia.edu/as/authorization.oauth2
      accessTokenUri: https://oauth.cc.columbia.edu/as/token.oauth2
      authorizationGrants: 
        - authorization_code
    scopes: 
      - openid
      - create
      - read
      - update
      - delete
      - auth-columbia
      - auth-facebook
      - auth-google
      - auth-linkedin 
      - auth-twitter
      - auth-windowslive
types:
  Thing: !include thingType.raml
/things:
  displayName: Things
  description: some things
  get:
    securedBy: # allow selection of one of columbia, facebook, or google login. 
      - oauth_2_0: { scopes: [ auth-columbia, openid, read ] }
      - oauth_2_0: { scopes: [ auth-google, openid, read ] }
    queryParameters:
     filter:
        description: |
          filter string
        type: string
        required: false
        example: |
          foobar
    responses:
      200:
        body:
          application/json:
            schema: Thing
  post:
    securedBy:
      - oauth_2_0: { scopes: [ openid, create, auth-columbia, demo-netphone-admin ] }
      - oauth_2_0: { scopes: [ openid, create, auth-google ] }
    responses:
      200:
        body:
          application/json:
            schema: Thing
  /{id}:
    get:
      securedBy:
        - oauth_2_0: { scopes: [ openid, read ] }
      responses:
        200:
          body:
            application/json:
              schema: Thing
    put:
      securedBy:
        - oauth_2_0: { scopes: [ openid, update ] }
      responses:
        200:
          body:
            application/json:
              schema: Thing
    /foo:
      get:
        securedBy:
          - oauth_2_0
        responses:
          200:
            body:
              application/json:
                schema: Thing
      post:
        securedBy:
          - oauth_2_0: { scopes: [ barfoo ] }
        responses:
          200:
            body:
              application/json:
                schema: Thing
"""

m = ramlParse(ramlString)
for k,v in m.items():
  print('"%s": "%s",'%(k.replace('&#x2F;','/'),v))
