import json
from flask import request, _request_ctx_stack
from functools import wraps
from jose import jwt
from urllib.request import urlopen


AUTH0_DOMAIN = 'awd.au.auth0.com'
ALGORITHMS = ['RS256']
API_AUDIENCE = 'app'


class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


def get_token_auth_header():
    try:
        headers = request.headers['Authorization']
        auth_header = headers.split()
        if auth_header[0].lower() == 'bearer':
            return auth_header[1]
    except:
        raise AuthError({"code": "Unauthorized", "description": "You don't have access to this resource"}, 401)


def check_permissions(permission, payload):
    if "permissions" not in payload:
        raise AuthError({'code': 'invalid_claims', 'description': 'Permissions not included in JWT.'}, 400)
    if permission not in payload['permissions']:
        raise AuthError({'code': 'unauthorized', 'description': 'Permission not found.'}, 401)
    else:
        return True


# soruce code: https://auth0.com/docs/quickstart/backend/python/01-authorization#validate-access-tokens
def verify_decode_jwt(token):
    jsonurl = urlopen("https://" + AUTH0_DOMAIN + "/.well-known/jwks.json")
    jwks = json.loads(jsonurl.read())
    unverified_header = jwt.get_unverified_header(token)
    rsa_key = {}
    for key in jwks["keys"]:
        if key["kid"] == unverified_header["kid"]:
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"]
            }
    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer="https://" + AUTH0_DOMAIN + "/"
            )
            return payload

        except jwt.ExpiredSignatureError:
            raise AuthError({"code": "token_expired", "description": "token is expired"}, 401)
        except jwt.JWTClaimsError:
            raise AuthError({"code": "invalid_claims", "description": "incorrect claims," 
                                                                      "please check the audience and issuer"}, 401)
        except Exception:
            raise AuthError({"code": "invalid_header", "description": "Unable to parse authentication"
                                                                      " token."}, 401)

        _request_ctx_stack.top.current_user = payload

    raise AuthError({"code": "invalid_header", "description": "Unable to find appropriate key"}, 401)


def requires_auth(permission=''):
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()
            payload = verify_decode_jwt(token)
            check_permissions(permission, payload)
            return f(payload, *args, **kwargs)
        return wrapper
    return requires_auth_decorator
