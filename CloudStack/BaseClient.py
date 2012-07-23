import urllib2
import urllib
import json
import hmac
import base64
import hashlib
import re
import ConfigParser
import os

env = os.environ["HOME"]
config_file = env + '/.cloudstack'
config = ConfigParser.ConfigParser()
config.read(config_file)

class BaseClient(object):
    def __init__(self):

        self.api = config.get("cloud", "api")
        self.apikey = config.get("cloud", "apikey")
        self.secret = config.get("cloud", "secret")

    def request(self, command, args):
        args['apikey']   = self.apikey
        args['command']  = command
        args['response'] = 'json'
        
        params=[]
        
        keys = sorted(args.keys())

        for k in keys:
            params.append(k + '=' + urllib.quote_plus(args[k])) 
       
        query = '&'.join(params)

        signature = base64.b64encode(hmac.new(
            self.secret, 
            msg=query.lower(), 
            digestmod=hashlib.sha1
        ).digest())

        query += '&signature=' + urllib.quote_plus(signature)

        response = ''

        try:
            global response
            response = urllib2.urlopen(self.api + '?' + query)
        except urllib2.HTTPError, e:
            print e.readline()
            exit()
        except urllib2.URLError, e:
            print e.readline()
            exit()
        except httplib.HTTPException, e:
            print e.readline()
            exit()

        decoded = json.loads(response.read())
       
        propertyResponse = command.lower() + 'response'
        if not propertyResponse in decoded:
            if 'errorresponse' in decoded:
                raise RuntimeError("ERROR: " + decoded['errorresponse']['errortext'])
            else:
                raise RuntimeError("ERROR: Unable to parse the response")

        response = decoded[propertyResponse]
        result = re.compile(r"^list(\w+)s").match(command.lower())

        if not result is None:
            type = result.group(1)

            if type in response:
                return response[type]
            else:
                # sometimes, the 's' is kept, as in :
                # { "listasyncjobsresponse" : { "asyncjobs" : [ ... ] } }
                type += 's'
                if type in response:
                    return response[type]

        return response
