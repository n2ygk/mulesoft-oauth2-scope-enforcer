# mulesoft-oauth2-scope-enforcer
MuleSoft custom API gateway policy enforcement of securedBy scopes

## Introduction
This Mulesoft API Gateway [custom policy](https://docs.mulesoft.com/api-manager/applying-custom-policies)
implements resource/method `securedBy` RAML scopes. It is meant to be added after one of the OAuth 2.0
Access Token enforcement policies has already validated the Access Token and put the token information into
the `_agwTokenContext` flowVar.

The reason this is needed is the MuleSoft standard policies currently only implement _global_ checking for
required scopes rather than for each specific resource and method:

![alt-text](global-scope-enforcement.png "screen shot of example of global scope enforcement policy")

One must provide a single list of scopes and can optionally indicated which resource pattern(s) and
method(s) to apply that scope to. However, RAML is much more expressive and typically would use
_different_ scopes for various resources and methods in an API:

```
#%RAML 1.0
title: demo
version: v1
baseUri: https://demo.com/{version}
securitySchemes: 
  oauth_2_0: !include oauth2.raml

/things:
  get:
    securedBy:
      - oauth_2_0: { scopes: [ openid, auth-columbia, read ] }
  post:
    securedBy:
      - oauth_2_0: { scopes: [ openid, auth-columbia, create ] }
  /{id}:
	get:
	  securedBy:
		- oauth_2_0: { scopes: [ openid, auth-columbia, read ] }
	put:
	  securedBy:
		- oauth_2_0: { scopes: [ openid, auth-columbia, update ] }
```

In this example, GET /things requires the `read` scope and POST /things requires the `create` scope and
PUT /things/{id} requires the `update` scope.

## Applying the Policy

![alt-text](applied-policy.png "screen shot of example policy being applied")

## Policy Developer Notes
The following are notes for developers of this Policy.

The end game is to pass in a URL to the RAML description and then parse the RAML to find the securedBy
and cache this into a map like this:

Initially just implement a JSON map of `{"method:resource": "scopes"}`, for example:

```
{
  "get:/things": "openid auth-columbia read",
  "post:/things": "openid auth-columbia create",
  "get:/things/{id}": "openid auth-columbia read",
  "put:/things": "openid auth-columbia update"
}
```

The RAML can be found at `/console/api/?raml` or in the API Developer Portal (subject to permissions
TBD):

![alt-text](developer-portal.raml.png "screen shot of developer portal showing ROOT RAML URL")


This naming is similar to what the MuleSoft APIkit router uses for flow names.

Example inbound scoped properties for `PUT /v1/api/things/123` which belongs to the APIkit flow named
`put:/things/{id}:api-config`:

```
http.listener.path=/v1/api/*
http.method=PUT
http.query.params=ParameterMap{[]}
http.query.string=
http.relative.path=/api/things/123
http.remote.address=/127.0.0.1:51589
http.request.path=/v1/api/things/123
http.request.uri=/v1/api/things/123
http.scheme=https
http.uri.params=ParameterMap{[id=[123]]}
```

N.B. looks like I can use the regex stuff for resources: https://docs.mulesoft.com/api-manager/add-rlp-support-task

- Do we make the policy map use wildcards or regexps to match URL parameters?

### Installing the Policy

Follow the Mulesoft instructions for adding custom policies, uploading the YAML and XML files.

### Developing and Testing Mulesoft Custom Policies in Anypoint Studio
See https://docs.mulesoft.com/anypoint-studio/v/6/studio-policy-editor and
https://docs.mulesoft.com/api-manager/creating-a-policy-walkthrough

Since we also use Anypoint Studio to test policies pushed from the Anypoint API Manager, there
can be some confusion about the API Autodiscovery mechanism and whether we are testing
our locally-developed policy (a beta feature of Studio 6.1) or one pushed down from API Manager.
There's nothing in the configuration that says which one to use, but it actually just works
as expected when you right-click on the policy and select Run As/API Custom Policy (configure):

![alt text](api-cust-policy.png "Run As API Custom Policy (configure)")

![alt text](api-cust-policy-config.png "Custom Policy Configuration Edit")

### Inconsistency across Mule implementations of OAuth 2.0

MuleSoft has three documented implementations of OAuth 2.0 token validation and there are inconsistencies
with how the result of a successful validation is made available to the downstream API app:

- The [external OAuth 2.0 token validation policy](https://docs.mulesoft.com/api-manager/external-oauth-2.0-token-validation-policy#obtaining-user-credentials)
  identifies the user as `_muleEvent.session.securityContext.authentication.principal.username` and suggests putting this in an X-Authenticated-Userid header
- The [OpenAM OAuth Token Enforcement policy](https://docs.mulesoft.com/api-manager/openam-oauth-token-enforcement-policy#obtaining-user-credentials)
  identifies the user as one of the following inboundProperties (HTTP headers) or flow variables:
  - X-AGW-userid for authorization code grant type, or
  - X-AGW-client_id for client credentials grant type
  - flowVars[\_agwUser] HashMap which includes uid, group and email keys.
- The [PingFederate OAuth Token Enforcement policy](https://docs.mulesoft.com/api-manager/pingfederate-oauth-token-enforcement-policy#obtaining-user-credentials)
  similarly to OpenAM uses the same values.

So, I conclude that the “standard” is what’s used for OpenAM and PingFederate.

**Additional observed flowVars:**

https://docs.mulesoft.com/release-notes/api-gateway-2.0.2-release-notes documents `flowVars[_agwTokenContext]` 
which on inspection is a String containing the returned JSON map.

I've also seen these flowVars inbound:
- \_client\_id
- \_client\_name


### CAVEATS
- **Consider this an Alpha test experimental version!**

### TO DO

## Author
Alan Crosswell

Copyright (c) 2017 The Trustees of Columbia University in the City of New York

## LICENSE
[Apache 2.0](LICENSE)

