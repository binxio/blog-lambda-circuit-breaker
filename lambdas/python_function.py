import botocore.vendored.requests as requests
from botocore.vendored.requests.auth import HTTPBasicAuth
from circuitbreaker import circuit, CircuitBreakerError
import json


@circuit(failure_threshold=2)
def send_request(url: str, user: str, pwd: str, req=None) -> (int, dict):
    print(f'Sending request to url={url}, req={req}')
    if req:
        resp = requests.post(url, json=req, auth=HTTPBasicAuth(user, pwd), verify=False, timeout=2)
    else:
        resp = requests.get(url, auth=HTTPBasicAuth(user, pwd), verify=False, timeout=2)
    try:
        body = resp.json()
        code = resp.status_code
    except Exception as e:
        print('Response contains no body')
        code = resp.status_code
        body = {}
    if code == 500:
        raise ValueError('Service returned 500')
    print(f'Received: body={body}, code={code}')
    return code, body


def response(code, body):
    return {
        'statusCode': code,
        'headers': {
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key',
            'Access-Control-Allow-Methods': '*',
            'Access-Control-Allow-Origin': '*',
        },
        'body': json.dumps(body)
    }


def handler(event, context):
    try:
        code, body = send_request('https://httpbin.org/status/500', 'username', 'password')
        return response(code, body)
    except CircuitBreakerError as err:
        return response(500, {
            'error_type': 'circuit-breaker',
            'error': str(err)
        })
    except Exception as err:
        return response(500, {
            'error_type': 'unknown-error',
            'error': str(err)
        })
