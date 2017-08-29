# mulesoft-oauth2-scope-enforcer
MuleSoft custom API gateway OAuth 2.0 scope enforcement policy

## Contents
- [Introduction](#introduction)
- [Installing the Policy](#installing-the-policy)
- [Applying the Policy](#applying-the-policy)
	- [Configuring Enterprise Scope Validation](#configuring-enterprise-scope-validation)
	- [Configuring resource and method required scopes](#configuring-resource-and-method-required-scopes)
	- [Configuring Method & Resource Conditions](#configuring-method--resource-conditions)
	- [Example Configuration with Enterprise Validation](#example-configuration-with-enterprise-validation)
	- [Configuring Logging](#configuring-logging)
	- [flowVars added](#flowvars-added)
	- [Errors](#errors)
- [Why this custom policy is required](#why-this-custom-policy-is-required)
- [Policy Developer Notes](#policy-developer-notes)
	- [Developing and Testing Mulesoft Custom Policies in Anypoint Studio](#developing-and-testing-mulesoft-custom-policies-in-anypoint-studio)
	- [Inconsistency across Mule implementations of OAuth 2.0](#inconsistency-across-mule-implementations-of-oauth-20)
	- [CAVEATS](#caveats)
	- [TODO](#todo)
- [Author](#author)
- [LICENSE](#license)

## Introduction
This Mulesoft API Gateway [custom policy](https://docs.mulesoft.com/api-manager/applying-custom-policies)
validates OAuth 2.0 required scopes for each method & resource and optionally adds _enterprise scope validation_
in which group memberships from the enterprise's authn/z system are intersected with granted
scopes to create _effective scope_ grants.

It is meant to be added after one of the `OAuth 2.0 Access Token enforcement` policies has already
validated the Access Token and put the token information into the `_agwTokenContext` flowVar.

## Installing the Policy

You must have API Manager privileges that allow you to install custom policies.
Follow the [Mulesoft instructions](https://docs.mulesoft.com/api-manager/add-custom-policy-task)
for adding custom policies, uploading the YAML and XML files.

## Applying the Policy

In API Manager for your app, select Policies/Apply New Policy and search for this custom policy. You
can narrow down the search by selecting Fulfills `OAuth 2.0 scope enforcement`.

![alt-text](search.png "screen shot of example of finding the custom OAuth 2.0 scope enforcement policy")

Note that this policy requires an _upstream_ `OAuth 2.0 protected` policy to be installed first.

### Configuring Enterprise Scope Validation
Provide the triggering scope and group attribute name. The triggering scope causes enterprise validation for
the given attribute that is in the OAuth 2.0 validation result's access\_token (\_agwTokenContext).
For example: `auth-columbia`:`group` is used when the `auth-columbia` scope is present and the
access_token contains a `group` attribute that is a list of "OAuth groups" the user is a member of.

The first matching triggering scope is used and any other matching triggers will be ignored. At least one of
the triggering scopes must be present in the Access Token's granted scopes. If no matching triggering scopes 
are present then a 403 Invalid Scope error will be returned.

This group list will be intersected with the OAuth 2.0 granted scope list to produce the _effective_ scope list
which will then be tested for scope enforcement.

Enterprise Scope Validation is a workaround for the inability of some (all) currently Mule-supported OAuth 2.0 service
providers to provide a mechanism to alter the granted scopes.

### Configuring resource and method required scopes

Paste a JSON policy document as produced by [ramlpolicy.py](./ramlpolicy.py)
(which parses the API's RAML file) or create one manually.

Configure the scope enforcement policy by adding method:resource keys and values that are the 
scopes you want to enforce for the given method:resource.
In this example, we add `get:/things` with three alternative lists of required scopes and so on.

The method:resource name is similar to what the MuleSoft APIkit router uses for flow names.

If you have a common (set of) scope(s) that you want enforced you can
repeat them here for each table entry, or list them in the prior `OAuth 2.0 protected` policy.

### Configuring Method & Resource Conditions

As with most newer (Mule 3.8.1+) API Policies, you can limit this Policy to apply only to
[specific resources and methods](https://docs.mulesoft.com/api-manager/resource-level-policies-about). This is
**a level above** this policy's own method:resource scope enforcement that simply identifies the
methods and resources for which this entire policy is applied. Yes, this is confusing! If you don't understand
this feature, just leave it set to "Apply configurations to all API methods & resources". That's probably
what you want.

### Example Configuration with Enterprise Validation

![alt-text](apply.png "screen shot of example of applying the custom OAuth 2.0 scope enforcement policy")

This example configuration enables enterprise scope validation whenever one of the `auth-columbia`,
`auth-facebook` or `auth-google` scopes is present by retrieving the `group` attribute,
which happens to be the same attribute all three identity providers in our configuration.

The granted scopes in the Access Token are interesected with the scopes in the
`group` list to become the _effective scopes_. If none of the `auth-*` is present 
in the granted scopes, the policy fails.

The following method:resource scopes were generated by [ramlpolicy.py](./ramlpolicy.py)
based on parsing the application's RAML API document:

```
{
  "post:/things": [["auth-columbia", "demo-netphone-admin", "create"],
                   ["auth-google", "create"],
                   ["auth-facebook", "create"]],
  "put:/things/.+": [["auth-columbia", "update"]],
  "get:/things": [["auth-columbia", "read"],
                  ["auth-google", "read"],
                  ["auth-facebook", "read"]],
  "get:/things/.+": [["read"]],
  "get:/things/.+/foo": []
}
```

You'll note that a POST to /things will succeed if the effective scopes matching any of the mutually
exclusive choices shown. The idea is to use the `auth-*` scope selectors which identify which identity
provider is used by the Authorization Code grant. Also note that the "get:/things/.+" scope doesn't require
any enterprise validation. That's allowed but is a non-sensical example.

Note that if you are using a Client Credentials grant, there is no user identified and this policy will fail
if enterprise scopes are configured. This can be a good mechanism to require a given API to use Authorization
Code grants.

### Configuring Logging

To debug this Policy change the logging level to DEBUG in log4j2.xml:
```xml
<AsyncLogger name="org.mule.module.scripting.component.Scriptable" level="DEBUG"/>
```

Some example debugging log messages follow:
```
DEBUG 2017-08-23 16:43:48,295 [[demo-echo].throttling-task.01] org.mule.module.scripting.component.Scriptable: Policy 236386: Access token (granted) scopes: "create demo-netphone-admin read openid auth-columbia"
DEBUG 2017-08-23 16:43:48,295 [[demo-echo].throttling-task.01] org.mule.module.scripting.component.Scriptable: Policy 236386: Enterprise validation scope alternatives: "auth-columbia | auth-facebook"
DEBUG 2017-08-23 16:43:48,297 [[demo-echo].throttling-task.01] org.mule.module.scripting.component.Scriptable: Policy 236386: Enterprise groups: "read openid create update auth-columbia delete"
DEBUG 2017-08-23 16:43:48,297 [[demo-echo].throttling-task.01] org.mule.module.scripting.component.Scriptable: Policy 236386: Enterprise validation results in effective scopes: "read openid auth-columbia create"
DEBUG 2017-08-23 16:43:48,301 [[demo-echo].throttling-task.01] org.mule.module.scripting.component.Scriptable: Policy 236386: Found a match in the scopeMap for "post:/things" requiring scopes: "create demo-netphone-admin"
DEBUG 2017-08-23 16:43:48,302 [[demo-echo].throttling-task.01] org.mule.module.scripting.component.Scriptable: Policy 236386: Access Token does not have one or more of the required enterprise scopes: create demo-netphone-admin
WARN  2017-08-23 16:43:48,329 [[demo-echo].throttling-task.01] org.mule.api.processor.LoggerMessageProcessor: Policy 236386 invalid_scope: Access Token does not have one or more of the required enterprise scopes: create demo-netphone-admin
```

### flowVars added
As a convenience, this policy also sets the following flowVars for use by subsequent modules in the flow:

  **scope**: (effective) list of granted scopes

  **requiredScopes**: list of required scopes configured by this policy for this method & resource

### Errors

This policy throws the following errors and in general "fails closed" which prevents inadvertent unprotected access.
Upon success it sets a 200 status and flow continues to the Mule app.

| Status | Error Code           | Error Description              | Possible causes         |
|:------:|----------------------|--------------------------------|-------------------------|
| 403    | invalid\_scope        | Access Token does not have the required [enterprise] scopes: %s | Client app didn't request one or more of the listed scopes or enterprise scope validation removed a required scope |
| 403    | invalid\_scope        | Access Token does not have any of the required enterprise scopes: %s | Enterprise scope validation was configured and none of the configuration validation triggering scopes was requested/granted |
| 403    | invalid\_scope        | required Access Token is missing | Method & Resource Conditions are set incorrectly in the upstream `OAuth 2.0 protected` policy (flowVars.\_agwTokenContext is not defined) |
| 503    | policy\_misconfigured | Enterprise validation attribute (%s) was not found in Access Token | The wrong attribute name was configured for the "OAuth group list" |
| 503    | policy\_misconfigured | request path (%s) has no required scopes: Configure Method & Resource conditions | A method:request was specified with a blank required scope list (which is impossible to configure, so how'd you end up here?). If you want a method:resource that requires `OAuth 2.0 protected` but with no scopes, use a Method & Resource condition here. If you want a method:resource that doesn't require `OAuth 2.0 protected` at all, use a Method & Resource scope in that Policy's configuration.|
| 503    | policy\_misconfigured | request path (%s) doesn't match listener path (%s) | impossible condition:-) Probably a bug in Policy code |
| 503    | policy\_misconfigured | unknown misconfiguration       | bug in Policy code      |


## Why this custom policy is required

The reason this custom policy is needed is that the MuleSoft standard policies currently only 
implement _global_ checking for
a static list of required scopes (which they misidentify as _supported scopes_) rather than allowing for
different required scopes for each specific method and resource as shown here:

![alt-text](global-scope-enforcement.png "screen shot of example of global scope enforcement policy")

One must provide a single list of scopes and can optionally indicate which resource pattern(s) and
method(s) to apply that scope to. However, RAML (and OpenAPI/Swagger) is (are)
much more expressive and typically would use
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

## Policy Developer Notes
The following are notes for developers of this Policy.

The end game is to pass in a URL to the RAML description and then parse the RAML to find the securedBy
and cache this into a map later. The current implementation develops that map offline and pastes it in
to the configration.

There was some confusion around whether all the scopes in a `securedBy` are _required_ for the
the method to be allowed to execute. This has been clarified as being the case although the
[RAML 1.0 spec](https://github.com/raml-org/raml-spec/blob/master/versions/raml-10/raml-10.md#applying-security-schemes
language is (was) unclear on this. See [this issue](https://github.com/raml-org/raml-spec/issues/557#issuecomment-323615958).

The RAML can be found at `/console/api/?raml` if the APIkit console is enabled
or in the API Developer Portal (subject to permissions TBD).

Developer workflow:

1. Run the API app in Anypoint Studio
2. ./ramlpolicy.py
3. Cut the output and paste into the policy configuration.

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

### Developing and Testing Mulesoft Custom Policies in Anypoint Studio
See https://docs.mulesoft.com/anypoint-studio/v/6/studio-policy-editor and
https://docs.mulesoft.com/api-manager/creating-a-policy-walkthrough

However, it seems when testing a custom policy in Studio, other policies are no longer applied. This
breaks things as we need the flowVars created by the upstream `OAuth 2.0 protected` policy.

Since it's hard to debug Python Code in the MuleSoft Jython world, use [test.py](./test.py) as a simple test harness:
Copy the configured Python code from the relevant XML file in `~/AnypointStudio/workspace/.mule/policies/` and
append it to test.py. You can see the name of the applied policy in the Console log, for example:
```
INFO  2017-08-28 11:56:27,479 [agw-policy-notifier.01] com.mulesoft.module.policies.lifecyle.PolicyRegistryLifecycleManager: Policy 25246-236386.xml was correctly applied
```

### Inconsistency across Mule implementations of OAuth 2.0

MuleSoft has three documented implementations of OAuth 2.0 token validation and there are inconsistencies
with how the result of a successful validation is made available to the downstream API app:

- The [external OAuth 2.0 token validation policy](https://docs.mulesoft.com/api-manager/external-oauth-2.0-token-validation-policy#obtaining-user-credentials)
  identifies the user as `_muleEvent.session.securityContext.authentication.principal.username` and suggests putting this in an X-Authenticated-Userid header
- The [OpenAM OAuth Token Enforcement policy](https://docs.mulesoft.com/api-manager/openam-oauth-token-enforcement-policy#obtaining-user-credentials)
  identifies the user as one of the following inboundProperties (HTTP headers) or flow variables:
  - `X-AGW-userid` user ID for authorization code grant type
  - `X-AGW-client_id` client ID
  - `flowVars[_agwUser]` HashMap which includes uid, group and email keys.
- The [PingFederate OAuth Token Enforcement policy](https://docs.mulesoft.com/api-manager/pingfederate-oauth-token-enforcement-policy#obtaining-user-credentials)
  similarly to OpenAM uses the same values.

**Additional observed, but undocumented, flowVars:**

[The deprecated API Gateway 2.0.2 release notes](https://docs.mulesoft.com/release-notes/api-gateway-2.0.2-release-notes) documents `flowVars[_agwTokenContext]` 
which on inspection is a String containing the returned JSON map. This flowVar is critical as it contains
the granted _scope_ list, among other things.

I've also seen these flowVars:
- `_client_id` ID of the registered client app
- `_client_name` name of the registered client app

So, I conclude that the “standard” is what’s used for OpenAM and PingFederate. If you are using some other
OAuth 2.0 token validation policy, this custom policy **will break** if \_agwTokenContext is not present.


### TODO
- Add a "wildcard" enterprise scope validation which allows for securedBy scopes that explicitly do not include one of the required alternatives. Or just change the enterprise scope part to not care if one isn't present? This is basically to allow Client Credentials or Authorization Code....
- consider refactoring Python into native Mule code
- Caching of method:url decision for performance
- add "late binding" of enterprise scopes via LDAP query (or similar) rather than carrying forward the (stale) groups that were valid at the initial authorization code grant.

## Author
Alan Crosswell

Copyright (c) 2017 The Trustees of Columbia University in the City of New York

## LICENSE

Licensed under the [Apache License, Version 2.0](LICENSE) (the "License"); you may not use this file
except in compliance with the License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
implied. See the License for the specific language governing
permissions and limitations under the License.



