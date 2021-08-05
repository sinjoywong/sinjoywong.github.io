import time
import hashlib
import random
import base64
import hmac
import requests

def get_auth_v4(base64_policy='', region='', secret_key=''):
    yyyymmdd = time.strftime("%Y%m%d",time.gmtime())
    string_to_sign = base64_policy
    date_key = hmac.new("AWS4%s"%secret_key, yyyymmdd, hashlib.sha256).digest()
    date_region_key = hmac.new(date_key, region, hashlib.sha256).digest()
    date_region_service_key = hmac.new(date_region_key, 's3', hashlib.sha256).digest()
    signing_key = hmac.new(date_region_service_key, 'aws4_request', hashlib.sha256).digest()
    signature = hmac.new(signing_key, string_to_sign,hashlib.sha256).hexdigest()
    return signature
    
region = '' # Need modification
secretId = '' # Need modification
secret_key = '' # Need modification
yyyymmdd = time.strftime("%Y%m%d", time.gmtime())
bucket = '' # Need modification
domainName = '' # Need modification
localPath = '' # Need modification
expiration = '2021-12-30T12:00:00Z' # Need modification
objPrefix = 'post-prefix/'# Need modification
objName = objPrefix + 'posted-obj' # Need modification

policy = """
{
  "expiration": "%s",
  "conditions": [
    {"bucket":"%s"},
    ["starts-with","$key","%s"],
    {"success_action_status":"200"},
    {"x-amz-credential":"%s/%s/%s/s3/aws4_request"},
    {"x-amz-algorithm":"AWS4-HMAC-SHA256"},
    {"x-amz-date":"%sT000000Z"},
  ]
}""" % (expiration, bucket, objPrefix, secretId, yyyymmdd, region, yyyymmdd)
form_data = dict()
form_data['key'] = objName
form_data['x-amz-credential'] = '%s/%s/%s/s3/aws4_request'%(secretId, yyyymmdd, region)
form_data['x-amz-algorithm'] = 'AWS4-HMAC-SHA256'
form_data['x-amz-date'] = '%sT000000Z'%yyyymmdd
form_data['success_action_status'] = '200'
form_data['policy'] = base64.b64encode(policy)
form_data['x-amz-signature'] = get_auth_v4(form_data['policy'], region=region, secret_key=secret_key)
files = {'file': open(localPath, 'rb')}
url = "http://%s.%s" % (bucket, domainName)
req = requests.Request('POST',
                       url,
                       data=form_data,
                       files=files)
prepared = req.prepare()
s = requests.Session()
r = s.send(prepared)
print r.url
print r.status_code
import pprint
pprint.pprint(r.headers)
print r.content