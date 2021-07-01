import json
from flask import request, _request_ctx_stack
from functools import wraps
from jose import jwt
from urllib.request import urlopen

#Auth0 information
AUTH0_DOMAIN = 'dev-3z3iwebp.us.auth0.com'
ALGORITHMS = ['RS256']
API_AUDIENCE = 'coffe'

## AuthError Exception
class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code

#Function to extract the header from the request and try to split the bearer and token parts 
#and make sure that bearer and token are avilable
def get_token_auth_header():
    #getting the header from the request
    authHeader = request.headers.get('Authorization', None)
    #making sure that the auth header is avilable
    if not authHeader:
        raise AuthError({
            'code': 'authorization_header_missing',
            'description': 'Authorization header is expected.'
        }, 401)
    #spliting the parts of the header
    header_parts = authHeader.split()
    #checking if bearer is avilable
    if header_parts[0].lower() != 'bearer':
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization header must start with "Bearer".'
        }, 401)
    #checking if both bearer and token is avilable
    elif len(header_parts) == 1:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Token not found.'
        }, 401)
    #checking if only the token and bearer are in the header
    elif len(header_parts) > 2:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization header must be bearer token.'
        }, 401)
    #returning the token
    return header_parts[1]

#Function from auth0 that verify the token and return
#the payload part of the token
def verify_decode_jwt(token):
    jsonurl = urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')
    jwks = json.loads(jsonurl.read())
    unverified_header = jwt.get_unverified_header(token)
    rsa_key = {}
    if 'kid' not in unverified_header:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization malformed.'
        }, 401)

    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }
    if rsa_key:
        try:
            #trying to extract hte payload from the token
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer='https://' + AUTH0_DOMAIN + '/'
            )
            #returning the payload
            return payload
        #rasing error if the token is expired
        except jwt.ExpiredSignatureError:
            raise AuthError({
                'code': 'token_expired',
                'description': 'Token expired.'
            }, 401)
        #rasing error if issuer or the audience doesn't match
        except jwt.JWTClaimsError:
            raise AuthError({
                'code': 'invalid_claims',
                'description': 'Incorrect claims. Please, check the audience and issuer.'
            }, 401)
        except Exception:
            raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to parse authentication token.'
            }, 401)
    #rasing error if the header isn't valid
    raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to find the appropriate key.'
            }, 401)


#Function to check if the permissions required is avilable in the payload part of the token
def check_permissions(permission, payload):
    #checking if the permissions part is avilable in the payload
    if 'permissions' not in payload:
        raise AuthError({
            'description': 'Permissions not included in JWT.',
            'code': 'invalid_claims'
        }, 401)
    #checking if the required permission is avilable
    if permission not in payload['permissions']:
        #rasing unauthorized error if the permission isn't avilable
        raise AuthError({
            'description': 'Permission not found.',
            'code': 'unauthorized'
        }, 401)
    #returning true that the permission is avilable
    return True

#the required auth decorator that makes sure that the token is real 
#and there is authorization and that the required permissions are avilable 
def requires_auth(permission=''):
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            #getting the token from the header
            token = get_token_auth_header()
            #checking if the token is real and getting the payload
            payload = verify_decode_jwt(token)
            #checking if the required permissions are avilable
            check_permissions(permission, payload)
            return f(payload, *args, **kwargs)
        return wrapper
    return requires_auth_decorator
