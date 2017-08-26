#!/usr/bin/env python
"""
ramlpolicy: Parse an API's RAML and generate a compact table for inclusion in the
API Manager custom OAuth 2.0 scope enforcement policy.
"""
import json
import re
import yaml
from pprint import pprint
import logging
from optparse import OptionParser
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning


log = logging.getLogger()
if not log.handlers:
  handler = logging.StreamHandler()
  formatter = logging.Formatter('%(levelname)-5s %(asctime)s %(message)s')
  handler.setFormatter(formatter)
  log.addHandler(handler)

httpVerbs = ['get','post','put','update','patch','delete']

# table of scopes defined in the securitySchemes
# N.B. MuleSoft APIkit currently has a bug that requries all possible scopes to be enumerated
# This is just plain wrong.
oauth2Scopes = {}

def securitySchemes(schemes):
  """
  Parse the securitySchemes to collect the OAuth 2.0 scheme names and scopes
  """
  for s in schemes:
    if 'type' in schemes[s]:
      if schemes[s]['type'].lower() == 'oauth 2.0':
        oauth2Scopes[s] = schemes[s]['scopes'] if 'scopes' in schemes[s] else []
      else:
        log.warn('securityScheme %s type %s not handled.'%(s,schemes[s]['type']))
  return

def securedBy(schemes): # the scheme name can be a string or a map key
  """
  Parse the securedBy list for the named OAuth 2.0 securitySchemes and use the default
  scopes or override them.
  """
  sl = []
  if not isinstance(schemes,list):
    log.warn('RAML parse error: securedBy expects a list')
    return sl
  for s in schemes:
    if isinstance(s,str): # if the node is terminal then no overriding scopes
      if s in oauth2Scopes:
        sl.append(oauth2Scopes[s]) # use the defaults for this scheme name
    else: # there _might_ be an override
      for k in s: # should be a dict with one key.
        if 'scopes' in s[k]:
          sl.append(s[k]['scopes'])
        else:
          if k in oauth2Scopes:
            sl.append(oauth2Scopes[s])
  return sl

rootScopes = []

def jsonParseRoot(j):
  """
  Parse root of document for securitySchemes definition and root securedBy
  """
  global rootScopes

  # document root securitySchemes definition
  if 'securitySchemes' in j:
    securitySchemes(j['securitySchemes'])
  # document root securedBy can set defaults for all methods that don't override with their own securedBy
  
  rootScopes = securedBy(j['securedBy']) if 'securedBy' in j else []

def jsonParseResource(j,resource,mustacheMap):
  """
  Recursively descend the JSON RAML API document looking for resources (e.g. /things), their
  associated methods (get, put, etc.) and optional securedBy. Also looks for securitySchemes
  to identity the names that are referenced in the securedBy and default scope values.

  URL parameters (e.g. /things/{id}) are rewritten as regular expressions (/things/.+).
  """
  #print(">>>>>>>>>>>>>>ENTER")
  #pprint(j)

  # iterate over keys at this level looking for a /resource and then below that method and under method securedBy
  for m in j:
    if isinstance(m,str): # ignore lists?
      if m[0] == '/':
        #print("<<<<<<<<<<<<<<<<<RECURSE %s"%resource+m)
        #pprint(j[m])
        mustacheMap = jsonParseResource(j[m],resource+m,mustacheMap)
      elif m in httpVerbs:
        method = m
        mkey = method + ':' + re.sub('{.+}','.+',resource)
        if 'securedBy' in j[m]:
          mustacheMap.update({mkey: securedBy(j[m]['securedBy'])})
        else:
          mustacheMap.update({mkey: rootScopes})
      else: 
        pass # ignore irrelevant keys
    else:
      log.debug('ignoring type %s'%type(m))
  return mustacheMap


### pull in from a URL
debugRamlString = """
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
  oauth_1_0:
    type: OAuth 1.0
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
# default top-level securedBy.
# Due to an APIkit bug that requires enumerating all possible scopes, you need to always
# override the scopes or end up with an impossible scope list.
securedBy:
  - oauth_2_0: { scopes: [] }
  - oauth_2_0: { scopes: [ root-default, auth-facebook, openid, read ] }
# above securedBy is use for /stuff get
/stuff:
  displayName: Stuff
  description: some stuff
  get:
    responses:
      200:
        body:
          application/json:
            schema: Stuff
  /more:
    displayName: moretuff
    description: some more stuff
    post:
      responses:
        200:
          body:
            application/json:
              schema: Stuff
/things:
  displayName: Things
  description: some things
  get:
    securedBy: # allow selection of one of columbia, facebook, or google login. 
      - oauth_2_0: { scopes: [ auth-columbia, openid, read ] }
      - oauth_2_0: { scopes: [ auth-facebook, openid, read ] }
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

# example root RAML is https://localhost:8082/v1/console/api/?raml
# and !include oauth2-ping.raml is https://localhost:8082/v1/console/api/oauth2-ping.raml

class RamlUrl:
  def __init__(self,url):
    self.url = url
    i = self.url.find('?raml')
    self.baseUrl = url[:i] if i > 0 else url
    if self.baseUrl[-1] != '/':
      self.baseUrl = self.baseUrl + '/' 
    yaml.add_constructor("!include", self.yaml_include)
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    logging.getLogger("requests").setLevel(logging.WARNING)

  def yaml_include(self, loader, node):
    log.debug('loading node %s'%node.value)
    response = requests.get(url=self.baseUrl+node.value,verify=False)
    if response.status_code == 200:
      return yaml.load(response.text)
    else:
      log.warn('HTTP request status %s: %s'%(response.status_code,response.reason))
      return None

  def load(self):
    log.debug('loading root node %s'%self.url)
    response = requests.get(url=self.url,verify=False)
    if response.status_code == 200:
      return yaml.load(response.text)
    else:
      log.warn('HTTP request status %s: %s'%(response.status_code,response.reason))
      return None
  

URL = 'https://localhost:8082/v1/console/api/?raml'
usage = '%%prog [options] [URL]\nURL is a RAML API definition [default: %s]'%URL
parser = OptionParser(usage=usage)
parser.add_option('-l','--loglevel',
                  type='string',
                  default='DEBUG',
                  help='log level [default: %default]')
parser.add_option('-d','--debug',
                  action = 'store_true',
                  help='debug with built-in RAML string')
(options,args) = parser.parse_args()

log.setLevel(options.loglevel)

if len(args) == 1:
  URL = args[0]
elif len(args) > 1:
  parser.print_help()
  exit(1)

if options.debug:
  y = yaml.load(debugRamlString)
else:
  y = RamlUrl(URL).load()

jsonParseRoot(y)
mustacheMap = {}
m = jsonParseResource(y,'',mustacheMap)
print(json.dumps(m))
