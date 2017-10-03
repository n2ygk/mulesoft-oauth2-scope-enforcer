// ramlpolicy.js: Parse a RAML 1.0 API definition and produce the JSON
// serialized object for use in OAuth 2.0 scope enforcement policy.
const {RamlJsonGenerator} = require('raml-json-enhance-node'); // https://github.com/mulesoft-labs/raml-json-enhance-node
// recursively descend the resource tree, building up the method & resource conditons as in this example:
//{
//  "post:/things": [["auth-columbia", "demo-netphone-admin", "create"],
//                   ["auth-google", "create"],
//                   ["auth-facebook", "create"]],
//  "put:/things/.+": [["auth-columbia", "update"]],
//  "get:/things": [["auth-columbia", "read"],
//                  ["auth-google", "read"],
//                  ["auth-facebook", "read"]],
//  "get:/things/.+": [["read"]],
//  "get:/things/.+/foo": []
//}
var scopeMap = {};
function Resource(resource) {
    var resPath = resource['parentUrl']+resource['relativeUri'];
    var methods = resource['methods']
    for (var m in methods) {
	var method = methods[m]['method']
	var securedBy = methods[m]['securedBy'];
	var re = /\{.*\}/g;
	var key = method + ':' + resPath.replace(re, '.+');
	scopeMap[key] = [];
	for (var s in securedBy) {
	    var scopes = securedBy[s]['settings']['scopes'];
	    var type = securedBy[s]['type'];
	    if (type == 'OAuth 2.0') {
		scopeMap[key].push(scopes);
	    }
	}
    }
    children = resource['resources'];
    for (var i in children) {
	Resource(children[i]);
    }
}
// start at the root of API's JSON document and invoke Resource() for each top-level resource.
function JsonGenerate(rootJson) {
    //console.log(rootJson['resources'][0]['methods'][0]['securedBy'][0]['settings']['scopes'])

    for (var i in rootJson['resources']) {
	resource = rootJson['resources'][i];
	Resource(resource);
    }

    console.log(JSON.stringify(scopeMap));
}

// Compile the RAML 1.0 file(s) into a JSON representation.
function RamlParse(raml) { 
    const generator = new RamlJsonGenerator(raml, {prettyPrint: false, verbose: false});
    promise = generator.generate()
    promise.then((json) => { JsonGenerate(json) });
}

// Pulling RAML from Anypoint Studio fails due to the self-signed cert, so ignore the error:
process.env.NODE_TLS_REJECT_UNAUTHORIZED = "0";
var defaultUrl = 'https://localhost:8082/v1/console/api/?raml' 
var url = defaultUrl;

if (process.argv[2] == '-h' || process.argv[2] == '--help') {
    console.log('Usage: ' + process.argv[1] + ' [raml URL] (default ' + defaultUrl + ')');
} else {
    if (process.argv.length == 3) {
	url = process.argv[2];
    }
    RamlParse(url);
}


