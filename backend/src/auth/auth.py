import json
from flask import request, _request_ctx_stack
from functools import wraps
from jose import jwt
from urllib.request import urlopen


AUTH0_DOMAIN = 'dev-os34dp82.us.auth0.com'
ALGORITHMS = ['RS256']
API_AUDIENCE = 'coffee'

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


def get_token_from_auth_header():
    """ Obtains the access token from the Authorization header """

    authorization_header = request.headers.get("Authorization", None)

    if not authorization_header:
        raise AuthError({
            "code": "authorization_header_missing",
            "description": "Authorization header missing."
        }, 401)

    parts = authorization_header.split()

    if parts[0].lower() != "bearer":
        raise AuthError({
            "code": "invalid_header",
            "description": "Authorization header must contain 'Bearer'"
        }, 401)

    if len(parts) == 1:
        raise AuthError({
            "code": "invalid_header",
            "description": "Token not found."
        }, 401)

    if len(parts) > 2:
        raise AuthError({
            "code": "invalid_header",
            "description": "Authorization header must have the format 'Bearer token'"
        }, 401)

    token = parts[1]
    return token


def check_permissions(permission, payload):
    """ Validate claims and check the requested permission """

    if "permissions" not in payload:
        raise AuthError({
            "code": "invalid_claims",
            "description": "Permissions not included in JWT."
        }, 400)

    if permission not in payload["permissions"]:
        raise AuthError({
            "code": "unauthorized",
            "description": "Permission not found."
        }, 403)

    return True


def verify_and_decode_jwt(token):
    """ Verify token is valid and return payload if valid """

    json_url = urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')
    jwks = json.loads(json_url.read())
    unverified_header = jwt.get_unverified_header(token)
    rsa_key = {}

    if 'kid' not in unverified_header:
        raise AuthError({
            "code": "invalid_header",
            "description": "Authorization malformed."
        }, 401)

    for key in jwks["keys"]:
        if unverified_header["kid"] == key["kid"]:
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
                issuer=f"https://{AUTH0_DOMAIN}/"
            )
            return payload

        except jwt.ExpiredSignatureError:
            raise AuthError({
                "code": "token_expired",
                "description": "Token expired."
            }, 401)
        except jwt.JWTClaimsError:
            raise AuthError({
                "code": "invalid_claims",
                "description": "Invalid claims. Please check the audience and issuer."
            }, 401)

        except Exception:
            raise AuthError({
                "code": "invalid_token",
                "description": "Unable to parse token."
            }, 400)
    raise AuthError({
        "code": "invalid_header",
        "description": "Unable to find the appropriate key."
    }, 400)


def requires_auth(permission=''):
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                token = get_token_from_auth_header()
                payload = verify_and_decode_jwt(token)
                check_permissions(permission, payload)
                return f(payload, *args, **kwargs)
            except AuthError as e:
                raise AuthError({
                    "code": "invalid_header",
                    "description": "Unable to find the appropriate key."
                }, 400)
        return wrapper
    return requires_auth_decorator



