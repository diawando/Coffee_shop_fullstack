import json
from flask import request, _request_ctx_stack, abort
from functools import wraps
from jose import jwt
from urllib.request import urlopen
from dotenv import load_dotenv
import os

load_dotenv()

AUTH0_DOMAIN = os.getev('AUTH0_DOMAIN')
ALGORITHMS = ['RS256']
API_AUDIENCE = os.get('API_AUDIENCE')

## AuthError Exception
'''
AuthError Exception
A standardized way to communicate auth failure modes
'''
class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


## Auth Header

#####################################################################################
#
#    Cette methode retourne la seconde partie du token et elemine le mot clé bearer
#
#####################################################################################
def get_token_auth_header():
   if 'Authorization' not in request.headers:
            abort(401)
   auth_header=request.headers['Authorization']
   header_parts=auth_header.split(' ')
   
   if len(header_parts)!=2:
       abort(401)

   #on verifie l'existence du mot clé dans le token
   elif header_parts[0].lower()!='bearer':
       abort(401, {'Your request does not contain the keyword bearer'})
       
   return header_parts[1]


#####################################################################################
#
#    Cette methode verifie l'existence de la permission dans le token (jwt)
#
#####################################################################################

def check_permissions(permission, payload):
    if 'permissions' not in payload:
            raise AuthError({
                 'code': 'invalid_claims',
                 'description': 'Permissions not included in JWT.'
            }, 400)
    
    if permission not in payload['permissions']:
        raise AuthError({
            'code': 'unauthorized',
            'description': 'Permission not found.'
        }, 403)
    return True

#####################################################################################
#
#    Cette methode verifie si le token envoyé par Auth0 est valide ou pas
#
#####################################################################################

def verify_decode_jwt(token):
    #OBTENIR LA CLÉ PUBLIQUE DEPUIS AUTH0
    jsonurl = urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')
    jwks = json.loads(jsonurl.read())
    
    #OBTENIR LES DONNÉES DANS LE HEADER
    unverified_header=jwt.get_unverified_header(token)
    
    #CHOISIR NOTRE CLÉ
    rsa_key = {}
    if 'kid' not in unverified_header:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization malformed.'
        }, 401)
        
    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            rsa_key = {
                'kty' : key['kty'],
                'kid' : key['kid'],
                'use' : key['use'],
                'n' : key['n'],
                'e' : key['e']
            }
    
    #VERIFICATION
    if rsa_key:
        try:
            #UTILISER LA CLÉ POUR VALIDER LE JWT
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer='https://' + AUTH0_DOMAIN + '/'
            )
            
            return payload
        
        except jwt.ExpiredSignatureError:
            raise AuthError({
                'code': 'token_expired',
                'description': 'Token expired.'
            },401)
            
        except jwt.JWTClaimsError:
            raise AuthError({
                'code': 'invalid_claims',
                'description': 'Incorrect claims. Please, check the audience and issuer.'
            }, 401)
        except Exception:
            raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to parse authentification token.'
            }, 400)
    raise AuthError({
         'code': 'invalid_header',
         'description': 'Unable to find the appropriate key.'
    }, 400)


def requires_auth(permission=''):
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()
            try:
                 payload = verify_decode_jwt(token)
            except:
                 abort(401)
            check_permissions(permission, payload)
            return f(payload, *args, **kwargs)
        return wrapper
    return requires_auth_decorator